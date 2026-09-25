import pytest
from httpx import AsyncClient

from tests.conftest import FakeLLMClient


@pytest.mark.asyncio
async def test_chat_returns_fixed_reply_when_knowledge_base_is_empty(client: AsyncClient) -> None:
    response = await client.post(
        "/chat", json={"message": "What is our leave policy?", "company_id": "acme", "session_id": "s1"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["grounded"] is False
    assert body["sources"] == []
    assert "don't have enough information" in body["answer"]


@pytest.mark.asyncio
async def test_chat_answers_from_indexed_content(client: AsyncClient, fake_llm_client: FakeLLMClient, app) -> None:
    from app.ingestion.chunker import Chunk

    vector_store = app.state.vector_store
    embedding_service = app.state.embedding_service
    text = "Employees get 24 paid leave days per year."
    vector = embedding_service.embed_documents([text])[0]
    vector_store.upsert_chunks(
        company_id="acme",
        document_id="doc-1",
        document_name="leave-policy.txt",
        chunks=[Chunk(text=text, source_name="leave-policy.txt", chunk_index=0, page=1)],
        vectors=[vector],
    )
    fake_llm_client.response_text = "You get 24 paid leave days per year."

    response = await client.post(
        "/chat", json={"message": text, "company_id": "acme", "session_id": "s1"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["grounded"] is True
    assert body["answer"] == "You get 24 paid leave days per year."
    assert body["sources"] == [{"document_name": "leave-policy.txt", "page": 1}]


@pytest.mark.asyncio
async def test_chat_persists_conversation_and_messages(client: AsyncClient) -> None:
    await client.post("/chat", json={"message": "Hello", "company_id": "acme", "session_id": "s-persist"})

    conversations = await client.get("/conversations", params={"company_id": "acme", "session_id": "s-persist"})
    assert conversations.status_code == 200
    convo_list = conversations.json()
    assert len(convo_list) == 1

    messages = await client.get(f"/conversations/{convo_list[0]['id']}/messages", params={"company_id": "acme"})
    assert messages.status_code == 200
    roles = [m["role"] for m in messages.json()]
    assert roles == ["user", "assistant"]


@pytest.mark.asyncio
async def test_chat_rejects_empty_message(client: AsyncClient) -> None:
    response = await client.post("/chat", json={"message": "", "company_id": "acme", "session_id": "s1"})
    assert response.status_code == 422
