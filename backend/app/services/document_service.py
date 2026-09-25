from dataclasses import replace
from pathlib import Path

from app.ingestion.chunker import chunk_blocks
from app.ingestion.cleaner import clean_text, strip_repeated_lines
from app.ingestion.parsers import parse_file
from app.models.document import DocumentStatus, KnowledgeDocument
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore


async def ingest_document(
    document: KnowledgeDocument,
    file_path: Path,
    embedding_service: EmbeddingService,
    vector_store: VectorStore,
    chunk_size: int,
    chunk_overlap: int,
) -> None:
    try:
        blocks = strip_repeated_lines(parse_file(file_path))

        cleaned_blocks = []
        for block in blocks:
            text = clean_text(block.text)
            if text:
                cleaned_blocks.append(replace(block, text=text))

        chunks = chunk_blocks(cleaned_blocks, chunk_size, chunk_overlap)
        if not chunks:
            raise ValueError("No extractable text found in this document")

        vectors = embedding_service.embed_documents([chunk.text for chunk in chunks])
        vector_store.upsert_chunks(
            company_id=document.company_id,
            document_id=str(document.id),
            document_name=document.filename,
            chunks=chunks,
            vectors=vectors,
        )

        document.status = DocumentStatus.INDEXED
        document.chunk_count = len(chunks)
        document.error_message = None
    except Exception as exc:  # noqa: BLE001 - any failure here should mark the doc failed, not crash the worker
        document.status = DocumentStatus.FAILED
        document.error_message = str(exc)
    finally:
        await document.save()
