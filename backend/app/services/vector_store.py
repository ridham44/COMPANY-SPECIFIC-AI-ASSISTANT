import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams

from app.core.config import Settings
from app.ingestion.chunker import Chunk

COLLECTION_NAME = "knowledge_chunks"
_ID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "company-knowledge-assistant")


@dataclass
class RetrievedChunk:
    document_id: str
    document_name: str
    content: str
    score: float
    page: int | None = None


class VectorStore(ABC):
    @abstractmethod
    def upsert_chunks(
        self,
        company_id: str,
        document_id: str,
        document_name: str,
        chunks: list[Chunk],
        vectors: list[list[float]],
    ) -> None: ...

    @abstractmethod
    def search(
        self, company_id: str, query_vector: list[float], top_k: int, score_threshold: float
    ) -> list[RetrievedChunk]: ...

    @abstractmethod
    def delete_document(self, company_id: str, document_id: str) -> None: ...


class QdrantVectorStore(VectorStore):
    def __init__(self, settings: Settings) -> None:
        if settings.qdrant_local_path == ":memory:":
            self._client = QdrantClient(location=":memory:")
        elif settings.qdrant_local_path:
            self._client = QdrantClient(path=settings.qdrant_local_path)
        else:
            self._client = QdrantClient(url=settings.qdrant_url)

        self._vector_size = settings.embedding_dimensions
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        if self._client.collection_exists(COLLECTION_NAME):
            return
        self._client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=self._vector_size, distance=Distance.COSINE),
        )
        self._client.create_payload_index(COLLECTION_NAME, field_name="company_id", field_schema="keyword")
        self._client.create_payload_index(COLLECTION_NAME, field_name="document_id", field_schema="keyword")

    def upsert_chunks(
        self,
        company_id: str,
        document_id: str,
        document_name: str,
        chunks: list[Chunk],
        vectors: list[list[float]],
    ) -> None:
        points = [
            PointStruct(
                id=str(uuid.uuid5(_ID_NAMESPACE, f"{document_id}:{chunk.chunk_index}")),
                vector=vector,
                payload={
                    "company_id": company_id,
                    "document_id": document_id,
                    "document_name": document_name,
                    "page": chunk.page,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.text,
                },
            )
            for chunk, vector in zip(chunks, vectors)
        ]
        self._client.upsert(collection_name=COLLECTION_NAME, points=points)

    def search(
        self, company_id: str, query_vector: list[float], top_k: int, score_threshold: float
    ) -> list[RetrievedChunk]:
        results = self._client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            query_filter=Filter(must=[FieldCondition(key="company_id", match=MatchValue(value=company_id))]),
            limit=top_k,
            score_threshold=score_threshold,
        ).points
        return [
            RetrievedChunk(
                document_id=point.payload["document_id"],
                document_name=point.payload["document_name"],
                content=point.payload["content"],
                score=point.score,
                page=point.payload.get("page"),
            )
            for point in results
        ]

    def delete_document(self, company_id: str, document_id: str) -> None:
        self._client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(key="company_id", match=MatchValue(value=company_id)),
                    FieldCondition(key="document_id", match=MatchValue(value=document_id)),
                ]
            ),
        )
