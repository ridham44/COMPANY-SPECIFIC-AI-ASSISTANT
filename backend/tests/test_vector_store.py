import pytest

from app.core.config import Settings
from app.ingestion.chunker import Chunk
from app.services.vector_store import QdrantVectorStore


@pytest.fixture
def vector_store() -> QdrantVectorStore:
    settings = Settings(qdrant_local_path=":memory:", embedding_dimensions=4)
    return QdrantVectorStore(settings)


def _chunk(text: str, index: int) -> Chunk:
    return Chunk(text=text, source_name="doc.txt", chunk_index=index, page=1)


def test_search_finds_the_closest_chunk(vector_store: QdrantVectorStore) -> None:
    vector_store.upsert_chunks(
        company_id="acme",
        document_id="doc-1",
        document_name="handbook.txt",
        chunks=[_chunk("leave policy", 0), _chunk("payroll schedule", 1)],
        vectors=[[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0]],
    )

    results = vector_store.search(
        company_id="acme", query_vector=[0.9, 0.1, 0.0, 0.0], top_k=5, score_threshold=-1.0
    )

    assert results[0].content == "leave policy"


def test_search_never_crosses_company_boundaries(vector_store: QdrantVectorStore) -> None:
    vector_store.upsert_chunks(
        company_id="acme",
        document_id="doc-1",
        document_name="acme.txt",
        chunks=[_chunk("acme secret roadmap", 0)],
        vectors=[[1.0, 0.0, 0.0, 0.0]],
    )
    vector_store.upsert_chunks(
        company_id="globex",
        document_id="doc-2",
        document_name="globex.txt",
        chunks=[_chunk("globex secret roadmap", 0)],
        vectors=[[1.0, 0.0, 0.0, 0.0]],
    )

    acme_results = vector_store.search(
        company_id="acme", query_vector=[1.0, 0.0, 0.0, 0.0], top_k=10, score_threshold=-1.0
    )

    assert len(acme_results) == 1
    assert acme_results[0].content == "acme secret roadmap"


def test_delete_document_removes_only_its_chunks(vector_store: QdrantVectorStore) -> None:
    vector_store.upsert_chunks(
        company_id="acme",
        document_id="doc-1",
        document_name="a.txt",
        chunks=[_chunk("keep me", 0)],
        vectors=[[1.0, 0.0, 0.0, 0.0]],
    )
    vector_store.upsert_chunks(
        company_id="acme",
        document_id="doc-2",
        document_name="b.txt",
        chunks=[_chunk("delete me", 0)],
        vectors=[[0.0, 1.0, 0.0, 0.0]],
    )

    vector_store.delete_document(company_id="acme", document_id="doc-2")

    results = vector_store.search(company_id="acme", query_vector=[0.5, 0.5, 0, 0], top_k=10, score_threshold=-1.0)
    assert [r.content for r in results] == ["keep me"]


def test_score_threshold_filters_out_weak_matches(vector_store: QdrantVectorStore) -> None:
    vector_store.upsert_chunks(
        company_id="acme",
        document_id="doc-1",
        document_name="a.txt",
        chunks=[_chunk("unrelated content", 0)],
        vectors=[[0.0, 0.0, 0.0, 1.0]],
    )

    results = vector_store.search(company_id="acme", query_vector=[1.0, 0.0, 0.0, 0.0], top_k=10, score_threshold=0.9)
    assert results == []
