# Backend

FastAPI app that answers questions from documents you upload (PDF/DOCX/TXT).

- `POST /documents/upload` - upload a file, it gets parsed, cleaned, chunked,
  embedded and stored in Qdrant in the background. `GET /documents` to list
  status, `DELETE`/`POST .../reindex` to manage them.
- `POST /chat` - asks a question, retrieves the closest chunks for that
  `company_id`, and has the LLM answer from them only. Returns
  `{answer, sources, grounded}`. If nothing relevant is found, it returns the
  fixed "not enough information" reply without calling the LLM at all.
- `GET/DELETE /conversations` - conversation history, per company + session.

Everything is scoped by `company_id` - every document, chunk and query
carries it, so one workspace never sees another's data.

The pieces are behind interfaces so they're swappable: `LLMClient`
(`app/services/llm_client.py`), `EmbeddingService`
(`app/services/embedding_service.py`), `VectorStore`
(`app/services/vector_store.py`).

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

Parser/chunker/cleaner/vector-store/RAG-pipeline tests are fully offline (a
fake embedding model, a fake LLM, Qdrant's in-memory mode). The `/chat` and
`/documents` route tests do need a reachable MongoDB (see `MONGO_URI` in
`.env`) since they exercise real Beanie models against a scratch database
that gets dropped after each test.

## Running it for real

```bash
cp .env.example .env
uvicorn app.main:app --reload
```

This needs:
- MongoDB reachable at `MONGO_URI`
- Either a Qdrant server at `QDRANT_URL`, or `QDRANT_LOCAL_PATH` set to a
  folder (no server needed - it's an embedded, file-backed instance)
- The embedding model downloaded on first startup (`EMBEDDING_MODEL`, a few
  hundred MB from Hugging Face)
- Ollama running with `LLM_MODEL` pulled, for the LLM to actually compose
  answers - see `/SETUP.md`. Without it, `/chat` still retrieves and returns
  sources, just with a "couldn't reach the language model" note instead of a
  generated answer.

```bash
curl -F "company_id=demo" -F "file=@/path/to/handbook.pdf" http://localhost:8000/documents/upload
curl "http://localhost:8000/documents?company_id=demo"
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"message": "What is our leave policy?", "company_id": "demo", "session_id": "test-1"}'
```

## Config

Everything tunable is an env var (`.env.example`), read via
`app/core/config.py`. Copy it to `.env` and edit.
