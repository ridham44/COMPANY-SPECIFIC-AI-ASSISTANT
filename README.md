# Company Knowledge Assistant

A private, self-hosted chatbot that answers questions from your own company
documents - nothing sent to OpenAI, Gemini, or any external AI API. Everything
runs locally: the LLM (Ollama), the embedding model, the vector store, the
database.

## What it does

**Knowledge Base** - upload PDF, DOCX, or TXT files. Each one gets parsed,
cleaned, split into chunks, embedded, and indexed automatically. The
Knowledge Base page shows upload status (processing/indexed/failed) and lets
you delete or re-index a document.

**Chat** - ask a question in plain English, get an answer with the source
document(s) cited underneath. If nothing in the knowledge base is relevant
enough, you get a fixed "I don't have enough information" reply instead of a
made-up answer - the LLM never gets called in that case. Conversations are
saved per session and can be revisited or deleted.

**Multi-tenant by design** - every document, chunk, and query carries a
`company_id`. Two different workspaces never see each other's data, at the
database and vector-store level, not just in the UI.

## How a question gets answered

1. The question is embedded and compared against every indexed chunk
   belonging to that `company_id`.
2. If nothing scores above a relevance threshold, you get the fixed
   "not enough information" reply. No LLM call happens.
3. Otherwise, the closest chunks are handed to the LLM with a system prompt
   that forbids using outside knowledge and tells it to ignore anything in
   the retrieved text or the question that looks like an instruction (basic
   prompt-injection defense).
4. The answer comes back with the source documents that were actually used.

## Stack

| Piece | Choice |
|---|---|
| API | FastAPI (Python, async) |
| LLM | Ollama, running locally (default: Qwen2.5-7B-Instruct) |
| Embeddings | Sentence Transformers (default: bge-small-en-v1.5) |
| Vector store | Qdrant (runs embedded/file-based locally, or as a server in prod) |
| Database | MongoDB via Motor/Beanie (documents, conversations) |
| Frontend | Next.js |

See [`docs/research.md`](docs/research.md) for why these were picked over
the alternatives, including hardware sizing for a 16GB CPU-only box.

## Repo layout

```
backend/    FastAPI app - ingestion, RAG pipeline, API routes, tests
frontend/   Next.js app - Knowledge Base page, Chat page
eval/       Retrieval hit-rate scoring, evaluation dataset
docs/       Research and design decisions
deploy/     Production docker/nginx config
```

## Running it

See [`SETUP.md`](SETUP.md) for the full walkthrough (MongoDB, the embedding
model, Ollama, the frontend). Short version:

```bash
# backend
cd backend
cp .env.example .env
python -m venv .venv && .venv/Scripts/activate  # or source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# frontend, in another terminal
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Then open http://localhost:3000. Without Ollama running, chat still
retrieves and cites the right sources - it just shows a note instead of a
generated answer until the LLM is pulled (see `SETUP.md`).

Backend tests (no model or network needed, beyond a reachable MongoDB for
a couple of route tests): `cd backend && pytest`.

## Status

Built and working end-to-end locally: upload, parsing, chunking, real
embeddings, retrieval with company isolation, and RAG chat with fallback
when the LLM isn't running. Not yet built: authentication (every request
currently takes `company_id` as a plain parameter, no login), the admin
role/audit-log system, the embeddable public widget, and the full evaluation
suite - these are later phases, not yet started.
