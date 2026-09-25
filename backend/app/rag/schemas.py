from pydantic import BaseModel


class SourceRef(BaseModel):
    document_name: str
    page: int | None = None


class ChatResult(BaseModel):
    answer: str
    sources: list[SourceRef]
    grounded: bool
