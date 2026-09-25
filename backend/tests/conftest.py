from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.services.llm_client import LLMClient


class FakeLLMClient(LLMClient):
    # stands in for Ollama in tests, no model or network needed

    def __init__(self, response_text: str = "This is a fake LLM response.") -> None:
        self.response_text = response_text
        self.last_messages: list[dict[str, str]] | None = None

    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
    ) -> AsyncIterator[str]:
        self.last_messages = messages
        for word in self.response_text.split(" "):
            yield word + " "

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
    ) -> str:
        self.last_messages = messages
        return self.response_text

    async def aclose(self) -> None:
        return None


@pytest.fixture
def fake_llm_client() -> FakeLLMClient:
    return FakeLLMClient()


@pytest_asyncio.fixture
async def client(fake_llm_client: FakeLLMClient) -> AsyncIterator[AsyncClient]:
    app = create_app()
    app.state.llm_client = fake_llm_client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
