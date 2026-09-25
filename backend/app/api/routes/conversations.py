from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.conversation import Conversation, Message
from app.rag.schemas import SourceRef

router = APIRouter(prefix="/conversations", tags=["conversations"])


class ConversationOut(BaseModel):
    id: str
    session_id: str


class MessageOut(BaseModel):
    role: str
    content: str
    sources: list[SourceRef]
    grounded: bool | None


async def _get_owned_conversation(conversation_id: str, company_id: str) -> Conversation:
    try:
        object_id = PydanticObjectId(conversation_id)
    except ValueError:
        raise HTTPException(404, "Conversation not found") from None

    conversation = await Conversation.get(object_id)
    if conversation is None or conversation.company_id != company_id:
        raise HTTPException(404, "Conversation not found")
    return conversation


@router.get("", response_model=list[ConversationOut])
async def list_conversations(company_id: str, session_id: str | None = None) -> list[ConversationOut]:
    if session_id:
        conversations = await Conversation.find(
            Conversation.company_id == company_id, Conversation.session_id == session_id
        ).to_list()
    else:
        conversations = await Conversation.find(Conversation.company_id == company_id).to_list()
    return [ConversationOut(id=str(c.id), session_id=c.session_id) for c in conversations]


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
async def get_messages(conversation_id: str, company_id: str) -> list[MessageOut]:
    await _get_owned_conversation(conversation_id, company_id)

    messages = await Message.find(Message.conversation_id == conversation_id).sort("created_at").to_list()
    return [MessageOut(role=m.role, content=m.content, sources=m.sources, grounded=m.grounded) for m in messages]


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str, company_id: str) -> dict[str, str]:
    conversation = await _get_owned_conversation(conversation_id, company_id)

    await Message.find(Message.conversation_id == conversation_id).delete()
    await conversation.delete()
    return {"status": "deleted"}
