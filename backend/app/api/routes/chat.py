from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.models.conversation import Conversation, Message
from app.rag.schemas import ChatResult

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    company_id: str
    session_id: str


@router.post("/chat", response_model=ChatResult)
async def chat(payload: ChatRequest, request: Request) -> ChatResult:
    conversation = await Conversation.find_one(
        Conversation.company_id == payload.company_id, Conversation.session_id == payload.session_id
    )
    if conversation is None:
        conversation = Conversation(company_id=payload.company_id, session_id=payload.session_id)
        await conversation.insert()

    await Message(conversation_id=str(conversation.id), role="user", content=payload.message).insert()

    result = await request.app.state.rag_pipeline.answer(payload.company_id, payload.message)

    await Message(
        conversation_id=str(conversation.id),
        role="assistant",
        content=result.answer,
        sources=result.sources,
        grounded=result.grounded,
    ).insert()

    return result
