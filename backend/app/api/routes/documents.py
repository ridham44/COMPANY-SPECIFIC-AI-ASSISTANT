from pathlib import Path
from uuid import uuid4

from beanie import PydanticObjectId
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.ingestion.parsers import SUPPORTED_EXTENSIONS
from app.models.document import DocumentStatus, KnowledgeDocument
from app.services.document_service import ingest_document

router = APIRouter(prefix="/documents", tags=["documents"])

MAGIC_BYTES = {
    ".pdf": b"%PDF",
    ".docx": b"PK\x03\x04",
}


class DocumentOut(BaseModel):
    id: str
    filename: str
    category: str | None
    status: DocumentStatus
    chunk_count: int
    error_message: str | None
    version: int

    @classmethod
    def from_doc(cls, doc: KnowledgeDocument) -> "DocumentOut":
        return cls(
            id=str(doc.id),
            filename=doc.filename,
            category=doc.category,
            status=doc.status,
            chunk_count=doc.chunk_count,
            error_message=doc.error_message,
            version=doc.version,
        )


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    company_id: str = Form(...),
    category: str | None = Form(None),
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
) -> DocumentOut:
    extension = Path(file.filename or "").suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {extension or 'unknown'}")

    contents = await file.read()
    if len(contents) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(400, f"File exceeds the {settings.max_upload_mb}MB limit")

    expected_magic = MAGIC_BYTES.get(extension)
    if expected_magic and not contents.startswith(expected_magic):
        raise HTTPException(400, "File content doesn't match its extension")

    storage_dir = Path(settings.storage_dir) / company_id
    storage_dir.mkdir(parents=True, exist_ok=True)
    file_path = storage_dir / f"{uuid4()}{extension}"
    file_path.write_bytes(contents)

    document = KnowledgeDocument(
        company_id=company_id,
        filename=file.filename or file_path.name,
        original_path=str(file_path),
        category=category,
    )
    await document.insert()

    background_tasks.add_task(
        ingest_document,
        document,
        file_path,
        request.app.state.embedding_service,
        request.app.state.vector_store,
        settings.chunk_size,
        settings.chunk_overlap,
    )

    return DocumentOut.from_doc(document)


@router.get("", response_model=list[DocumentOut])
async def list_documents(company_id: str) -> list[DocumentOut]:
    docs = await KnowledgeDocument.find(KnowledgeDocument.company_id == company_id).to_list()
    return [DocumentOut.from_doc(doc) for doc in docs]


async def _get_owned_document(document_id: str, company_id: str) -> KnowledgeDocument:
    try:
        object_id = PydanticObjectId(document_id)
    except ValueError:
        raise HTTPException(404, "Document not found") from None

    document = await KnowledgeDocument.get(object_id)
    if document is None or document.company_id != company_id:
        raise HTTPException(404, "Document not found")
    return document


@router.delete("/{document_id}")
async def delete_document(document_id: str, company_id: str, request: Request) -> dict[str, str]:
    document = await _get_owned_document(document_id, company_id)

    request.app.state.vector_store.delete_document(company_id, document_id)
    Path(document.original_path).unlink(missing_ok=True)
    await document.delete()
    return {"status": "deleted"}


@router.post("/{document_id}/reindex", response_model=DocumentOut)
async def reindex_document(
    document_id: str,
    company_id: str,
    background_tasks: BackgroundTasks,
    request: Request,
    settings: Settings = Depends(get_settings),
) -> DocumentOut:
    document = await _get_owned_document(document_id, company_id)

    request.app.state.vector_store.delete_document(company_id, document_id)
    document.status = DocumentStatus.PROCESSING
    document.error_message = None
    await document.save()

    background_tasks.add_task(
        ingest_document,
        document,
        Path(document.original_path),
        request.app.state.embedding_service,
        request.app.state.vector_store,
        settings.chunk_size,
        settings.chunk_overlap,
    )
    return DocumentOut.from_doc(document)
