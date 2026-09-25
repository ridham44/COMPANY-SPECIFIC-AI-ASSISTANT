import logging

import httpx

from app.rag.generator import generate_answer
from app.rag.retriever import Retriever
from app.rag.schemas import ChatResult, SourceRef
from app.services.llm_client import LLMClient
from app.services.vector_store import RetrievedChunk

logger = logging.getLogger(__name__)

NO_LLM_REPLY = (
    "I found relevant information but couldn't reach the language model to write an answer "
    "(it may not be running yet). Here's what the knowledge base has on this:"
)


class RagPipeline:
    def __init__(
        self,
        retriever: Retriever,
        llm_client: LLMClient,
        no_answer_reply: str,
        llm_temperature: float,
    ) -> None:
        self._retriever = retriever
        self._llm_client = llm_client
        self._no_answer_reply = no_answer_reply
        self._llm_temperature = llm_temperature

    async def answer(self, company_id: str, query: str) -> ChatResult:
        chunks = await self._retriever.retrieve(company_id, query)
        if not chunks:
            return ChatResult(answer=self._no_answer_reply, sources=[], grounded=False)

        sources = _dedupe_sources(chunks)
        try:
            answer_text = await generate_answer(self._llm_client, query, chunks, self._llm_temperature)
        except httpx.HTTPError:
            logger.warning("LLM unreachable, falling back to source-only reply")
            bullets = "\n".join(f"- {s.document_name}" + (f" (page {s.page})" if s.page else "") for s in sources)
            answer_text = f"{NO_LLM_REPLY}\n{bullets}"

        return ChatResult(answer=answer_text, sources=sources, grounded=True)


def _dedupe_sources(chunks: list[RetrievedChunk]) -> list[SourceRef]:
    seen: set[tuple[str, int | None]] = set()
    sources = []
    for chunk in chunks:
        key = (chunk.document_name, chunk.page)
        if key in seen:
            continue
        seen.add(key)
        sources.append(SourceRef(document_name=chunk.document_name, page=chunk.page))
    return sources
