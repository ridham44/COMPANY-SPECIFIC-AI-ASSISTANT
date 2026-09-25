from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.services.llm_client import LLMClient

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


def get_llm_client(request: Request) -> LLMClient:
    return request.app.state.llm_client


@router.post("/chat")
async def chat(payload: ChatRequest, request: Request) -> StreamingResponse:
    llm_client = get_llm_client(request)
    messages = [{"role": "user", "content": payload.message}]

    async def token_stream():
        async for chunk in llm_client.stream_chat(messages):
            yield chunk

    return StreamingResponse(token_stream(), media_type="text/plain")
