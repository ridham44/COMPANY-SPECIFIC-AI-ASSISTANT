import hashlib
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.db import init_db
from app.main import create_app
from app.rag.pipeline import RagPipeline
from app.rag.retriever import Retriever
from app.services.llm_client import LLMClient
from app.services.vector_store import QdrantVectorStore

TEST_MONGO_DB_NAME = "company_assistant_test"
TEST_EMBEDDING_DIMENSIONS = 16


class FakeLLMClient(LLMClient):
    def __init__(self, response_text: str = "This is a fake LLM response.") -> None:
        self.response_text = response_text
        self.last_messages: list[dict[str, str]] | None = None

    async def stream_chat(self, messages, temperature=None):
        self.last_messages = messages
        for word in self.response_text.split(" "):
            yield word + " "

    async def chat(self, messages, temperature=None):
        self.last_messages = messages
        return self.response_text

    async def aclose(self) -> None:
        return None


class FakeEmbeddingService:
    """Hashes text into a deterministic vector - no model download needed for tests."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)

    @staticmethod
    def _vector(text: str) -> list[float]:
        digest = hashlib.sha256(text.encode()).digest()
        return [b / 255 for b in digest[:TEST_EMBEDDING_DIMENSIONS]]


@pytest.fixture
def fake_llm_client() -> FakeLLMClient:
    return FakeLLMClient()


@pytest_asyncio.fixture
async def mongo_client():
    settings = get_settings().model_copy(update={"mongo_db_name": TEST_MONGO_DB_NAME})
    client = await init_db(settings)
    yield client
    await client.drop_database(TEST_MONGO_DB_NAME)
    client.close()


@pytest_asyncio.fixture
async def app(fake_llm_client: FakeLLMClient, mongo_client):
    application = create_app()
    application.state.llm_client = fake_llm_client

    settings = get_settings().model_copy(
        update={"qdrant_local_path": ":memory:", "embedding_dimensions": TEST_EMBEDDING_DIMENSIONS}
    )
    embedding_service = FakeEmbeddingService()
    vector_store = QdrantVectorStore(settings)
    retriever = Retriever(embedding_service, vector_store, top_k=5, score_threshold=0.3)

    application.state.embedding_service = embedding_service
    application.state.vector_store = vector_store
    application.state.rag_pipeline = RagPipeline(
        retriever, fake_llm_client, settings.no_answer_reply, settings.llm_temperature
    )
    return application


@pytest_asyncio.fixture
async def client(app) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
