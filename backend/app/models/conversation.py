from datetime import datetime, timezone

from beanie import Document
from pydantic import Field

from app.rag.schemas import SourceRef


class Conversation(Document):
    company_id: str
    session_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "conversations"


class Message(Document):
    conversation_id: str
    role: str
    content: str
    sources: list[SourceRef] = Field(default_factory=list)
    grounded: bool | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "messages"
