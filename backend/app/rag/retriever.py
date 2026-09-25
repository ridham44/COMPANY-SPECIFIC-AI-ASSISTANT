import asyncio

from app.services.embedding_service import EmbeddingService
from app.services.vector_store import RetrievedChunk, VectorStore


class Retriever:
    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        top_k: int,
        score_threshold: float,
    ) -> None:
        self._embedding_service = embedding_service
        self._vector_store = vector_store
        self._top_k = top_k
        self._score_threshold = score_threshold

    async def retrieve(self, company_id: str, query: str) -> list[RetrievedChunk]:
        query_vector = await asyncio.to_thread(self._embedding_service.embed_query, query)
        return await asyncio.to_thread(
            self._vector_store.search, company_id, query_vector, self._top_k, self._score_threshold
        )
