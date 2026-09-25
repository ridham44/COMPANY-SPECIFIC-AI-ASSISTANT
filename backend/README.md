# Backend

FastAPI app with a `/chat` endpoint that streams replies from a local Ollama
model, plus `/health`. The LLM is called through `LLMClient`
(`app/services/llm_client.py`) so we can swap the model or runtime later
without touching the routes.

## Tests

Tests run against `FakeLLMClient` (`tests/conftest.py`), no model or network
needed.

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

## Running it for real

Needs an actual machine with enough RAM to hold the model — see
`/SETUP.md` at the project root for the full walkthrough.

```bash
docker compose up -d --build
docker compose exec ollama ollama pull qwen2.5:7b-instruct-q4_K_M

curl -N -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is our leave policy?"}'
```

`curl -N` just stops curl from buffering so you can see it stream.

## Config

Everything tunable is an env var (`.env.example`), read via
`app/core/config.py`. Copy it to `.env` and edit.
