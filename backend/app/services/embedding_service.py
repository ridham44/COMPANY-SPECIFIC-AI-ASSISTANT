from abc import ABC, abstractmethod

from app.core.config import Settings


class EmbeddingService(ABC):
    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    @abstractmethod
    def embed_query(self, text: str) -> list[float]: ...


class SentenceTransformerEmbeddingService(EmbeddingService):
    def __init__(self, settings: Settings) -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(settings.embedding_model)
        # bge models expect this prefix on the query side to get good retrieval quality
        self._query_prefix = (
            "Represent this sentence for searching relevant passages: "
            if "bge" in settings.embedding_model.lower()
            else ""
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        vector = self._model.encode([self._query_prefix + text], normalize_embeddings=True)[0]
        return vector.tolist()
