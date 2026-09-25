import pytest
from httpx import AsyncClient

from tests.conftest import FakeLLMClient


@pytest.mark.asyncio
async def test_chat_streams_response(client: AsyncClient, fake_llm_client: FakeLLMClient) -> None:
    async with client.stream("POST", "/chat", json={"message": "Hello"}) as response:
        assert response.status_code == 200
        chunks = [chunk async for chunk in response.aiter_text()]

    full_text = "".join(chunks)
    assert full_text.strip() == fake_llm_client.response_text.strip()


@pytest.mark.asyncio
async def test_chat_passes_user_message_to_llm(client: AsyncClient, fake_llm_client: FakeLLMClient) -> None:
    async with client.stream("POST", "/chat", json={"message": "What is our leave policy?"}) as response:
        assert response.status_code == 200
        async for _ in response.aiter_text():
            pass

    assert fake_llm_client.last_messages == [{"role": "user", "content": "What is our leave policy?"}]


@pytest.mark.asyncio
async def test_chat_rejects_empty_message(client: AsyncClient) -> None:
    response = await client.post("/chat", json={"message": ""})
    assert response.status_code == 422
