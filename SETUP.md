# Setup on the main PC

Steps to get this running on the actual machine (not the dev laptop). Do
this after pulling the repo there.

## 1. Requirements on that machine

- Docker + Docker Compose
- ~16GB RAM free, no GPU needed
- ~10GB free disk for the model + containers

## 2. Pull the repo

```bash
git clone <repo-url>
cd "COMPANY-SPECIFIC AI ASSISTANT"
```

## 3. Set up env vars

```bash
cd backend
cp .env.example .env
cd ..
```

Defaults in `.env.example` are fine to start with. `LLM_MODEL` and
`EMBEDDING_MODEL` there control which models get used — change these if you
want a different model later without touching any code.

## 4. Build and start the containers

```bash
docker compose up -d --build
```

This starts the backend and an empty Ollama server. No model is downloaded
by this step.

Check it's up:

```bash
docker compose ps
curl http://localhost:8000/health
```

## 5. Pull the LLM (this is the actual download, do it once)

```bash
docker compose exec ollama ollama pull qwen2.5:7b-instruct-q4_K_M
```

This is a few GB, give it time depending on the connection. You only need to
do this once — it's stored in the `ollama_data` volume and survives
restarts.

To check it downloaded:

```bash
docker compose exec ollama ollama list
```

## 6. Test the chat endpoint

```bash
curl -N -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, are you working?"}'
```

You should see a streamed reply. If it hangs or errors, check logs:

```bash
docker compose logs -f backend
docker compose logs -f ollama
```

## Swapping the model later

If this machine can handle something bigger/smaller than the default:

1. Pull the new model: `docker compose exec ollama ollama pull <model-name>`
2. Update `LLM_MODEL` in `backend/.env` (and in `docker-compose.yml` if you
   set it there too)
3. Restart the backend: `docker compose restart backend`

No code changes needed for this — the model name is just config.

## Stopping / restarting

```bash
docker compose stop        # keeps everything, just stops containers
docker compose up -d       # starts them back up
docker compose down        # removes containers, but keeps the volumes (model stays downloaded)
```

Don't run `docker compose down -v` unless you actually want to wipe the
downloaded model and Mongo/Qdrant data too — that flag removes volumes.

## Notes

- None of this should be run on a low-spec dev machine — the model won't
  fit/run well below ~16GB RAM. Development and testing (`pytest`) don't
  need the model at all, see `backend/README.md`.
- As later phases add Mongo/Qdrant services to `docker-compose.yml`, this
  file's steps stay the same, just with more containers coming up in step 4.
