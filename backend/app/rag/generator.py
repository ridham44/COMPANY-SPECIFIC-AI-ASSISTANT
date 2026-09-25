from app.rag.prompt_builder import build_messages
from app.services.llm_client import LLMClient
from app.services.vector_store import RetrievedChunk


async def generate_answer(
    llm_client: LLMClient, query: str, chunks: list[RetrievedChunk], temperature: float
) -> str:
    messages = build_messages(query, chunks)
    return await llm_client.chat(messages, temperature=temperature)
