from datetime import datetime, timezone
from enum import StrEnum

from beanie import Document
from pydantic import Field


class DocumentStatus(StrEnum):
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class KnowledgeDocument(Document):
    company_id: str
    filename: str
    original_path: str
    category: str | None = None
    status: DocumentStatus = DocumentStatus.PROCESSING
    chunk_count: int = 0
    error_message: str | None = None
    version: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "documents"
