chec# Setup on the main PC

Steps to get the whole thing running on the actual machine. Do this after
pulling the repo there.

## 1. Requirements on that machine

- Python 3.11+, Node 18+
- Docker + Docker Compose (only needed for Ollama - Mongo/Qdrant can run
  without it, see below)
- ~16GB RAM free, no GPU needed
- ~10GB free disk for the model + data

## 2. Pull the repo

```bash
git clone <repo-url>
cd "COMPANY-SPECIFIC AI ASSISTANT"
```

## 3. MongoDB

Either install MongoDB Community Server directly (no Docker needed - this is
what was used during development), or run it in a container:

```bash
docker run -d -p 27017:27017 --name mongo mongo:7
```

## 4. Backend

```bash
cd backend
cp .env.example .env
python -m venv .venv
.venv/Scripts/activate   # or `source .venv/bin/activate` on Linux/Mac
pip install -r requirements.txt
```

`QDRANT_LOCAL_PATH` in `.env` defaults to `./qdrant_data` - a plain folder,
no Qdrant server required. If you'd rather run a real Qdrant server (e.g. in
production, see `docker-compose.yml`), clear that env var and set
`QDRANT_URL` instead.

Start it:

```bash
uvicorn app.main:app --reload
```

First startup downloads the embedding model (`EMBEDDING_MODEL` in `.env`,
a few hundred MB from Hugging Face) - only happens once, it's cached after.

Check it's up:

```bash
curl http://localhost:8000/health
```

## 5. Ollama (the actual LLM)

This is the one piece that needs Docker and a real download - do it once,
on this machine:

```bash
docker run -d -p 11434:11434 -v ollama_data:/root/.ollama --name ollama ollama/ollama
docker exec ollama ollama pull qwen2.5:7b-instruct-q4_K_M
```

Without this step, `/chat` still works end to end (upload, search, retrieval)
but returns retrieved sources with a "couldn't reach the language model" note
instead of a generated answer.

## 6. Frontend

```bash
cd ../frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Open http://localhost:3000 - upload a document on the Knowledge Base page,
then ask about it on the Chat page.

## Swapping the model later

1. Pull the new model: `docker exec ollama ollama pull <model-name>`
2. Update `LLM_MODEL` in `backend/.env`
3. Restart the backend

No code changes needed - the model name is just config. Same goes for
`EMBEDDING_MODEL`, though changing that means re-indexing existing documents
since old and new embeddings aren't comparable.

## Production deployment

`docker-compose.yml` at the repo root brings up the backend + Ollama in
containers for a more permanent setup; Mongo/Qdrant services can be added the
same way once you're past local dev. See `backend/README.md` for the
per-service config knobs.
