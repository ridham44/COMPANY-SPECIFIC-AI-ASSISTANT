# Phase 1: Research & Stack Decisions

**Target hardware (as specified):** CPU-only server, 16GB RAM, no GPU.

This single fact drives most decisions below: no VRAM means every LLM must run
quantized on CPU via Ollama's llama.cpp backend, and model size must leave
headroom for the OS, embedding model, Qdrant, MongoDB and FastAPI to run
concurrently on the same 16GB. As a rule of thumb, a Q4_K_M GGUF needs
roughly (parameter count × 0.6-0.7 GB) of RAM at rest, plus ~1-2GB of context
KV cache at moderate context lengths. That leaves a practical ceiling of
**~8B parameters at Q4** as the safe default on this box, with 13B+ possible
but slow and risking swap under concurrent load.

---

## 1. LLMs (Ollama-runnable)

| Model | Quality (general/RAG-following) | RAM @ Q4_K_M | RAM @ Q8_0 | Speed on 16GB CPU box | Licence |
|---|---|---|---|---|---|
| **Qwen2.5-7B-Instruct** | Very strong instruction following, good at "answer only from context," strong multilingual | ~4.7 GB | ~8.1 GB | ~6-10 tok/s on modern 8-core CPU | Apache 2.0 |
| **Llama-3.1-8B-Instruct** | Strong general reasoning, solid grounding when prompted well | ~4.9 GB | ~8.5 GB | ~5-9 tok/s | Llama 3.1 Community License (usage restrictions >700M MAU, attribution required) |
| **Mistral-7B-Instruct-v0.3** | Good general quality, historically slightly weaker at strict "don't use outside knowledge" instructions than Qwen | ~4.4 GB | ~7.7 GB | ~6-10 tok/s | Apache 2.0 |
| **Gemma-2-9B-Instruct** | Strong quality, but 9B pushes past comfortable headroom on 16GB when Qdrant/Mongo are also running | ~5.8 GB | ~9.8 GB | ~4-7 tok/s (heavier) | Gemma Terms of Use (custom, has usage restrictions) |

**Recommendation:** **Qwen2.5-7B-Instruct, Q4_K_M** as the default `LLM_MODEL`.
It has the best track record among these for following strict "only answer
from the provided context" system prompts (important for our anti-hallucination
requirement), fits comfortably in 16GB alongside the rest of the stack, and is
Apache 2.0 (no usage-restriction fine print, unlike Llama/Gemma). Keep
`LLM_MODEL` as a config value so a smaller model (e.g. Qwen2.5-3B) can be
swapped in if latency under concurrent users becomes a problem, or a larger
one (e.g. Qwen2.5-14B) if a RAM upgrade happens later.

---

## 2. Embedding models (Sentence Transformers)

| Model | Retrieval quality (MTEB-style) | Dimensions | Size | Speed on CPU |
|---|---|---|---|---|
| **BAAI/bge-small-en-v1.5** | Good — strong for its size, purpose-built for retrieval (uses query/passage instruction prefixes) | 384 | ~130 MB | Fastest of the three; best fit for CPU-only |
| **intfloat/e5-small-v2** | Good, comparable to bge-small, also instruction-prefixed (`query:` / `passage:`) | 384 | ~130 MB | Fast, similar to bge-small |
| **sentence-transformers/all-MiniLM-L6-v2** | Decent general-purpose, but noticeably behind bge/e5 on retrieval-specific benchmarks | 384 | ~90 MB | Fastest, but quality tradeoff isn't worth it here |
| *(reference, not default)* BAAI/bge-base-en-v1.5 | Better than bge-small, ~2-3 points higher retrieval accuracy | 768 | ~440 MB | ~2-3x slower than the small variants |

**Recommendation:** **BAAI/bge-small-en-v1.5** as the default
`EMBEDDING_MODEL`. On a CPU-only 16GB box, embedding speed matters for both
ingestion throughput and query latency, and bge-small gives the best
quality-per-CPU-cycle of the small models. If eval results (see the script
below) show retrieval hit-rate is too low once real company data is loaded,
the upgrade path is `bge-base-en-v1.5` (also configurable, no code change
needed — just re-embed and re-index).

---

## 3. Vector database: Qdrant vs pgvector vs Chroma vs FAISS

| | Qdrant | pgvector | Chroma | FAISS |
|---|---|---|---|---|
| Deployment | Standalone service, Docker-friendly | Extension on existing Postgres | Standalone service or embedded | Library only, no server |
| Filtering (needed for mandatory `company_id` isolation) | Native payload filtering, indexed, fast | SQL `WHERE` filters, fine but needs careful indexing | Metadata filtering, less mature | None built-in — must be implemented manually alongside vectors |
| Multi-tenancy safety | Payload index + filter is a first-class, well-tested pattern | Achievable but relies on correct SQL every time | Workable, less battle-tested at scale | Would require rolling your own filter logic — highest risk of a leak bug |
| Ops overhead on a small self-hosted box | One extra container, low RAM footprint, simple API | None if Postgres already exists; adds one if not | One extra container | None (in-process), but no persistence/replication story out of the box |
| Delete/re-index by `document_id` | Native, simple | Native via SQL DELETE | Supported | Manual (rebuild index) |

**Recommendation: Qdrant.** It gives us mandatory, indexed `company_id`
filtering as a first-class primitive (directly matching non-negotiable rule
#2), runs as a lightweight standalone container appropriate for a small
self-hosted box, and has clean delete-by-filter and payload-index support for
the versioned re-indexing workflow in Phase 4. FAISS is ruled out because
company isolation would have to be hand-rolled, which is an unacceptable risk
for a hard multi-tenancy requirement. pgvector is a reasonable second choice
only if Postgres were already mandatory elsewhere in the stack — it isn't.

---

## 4. Inference runtime: Ollama vs llama.cpp vs vLLM

| | Ollama | llama.cpp (raw) | vLLM |
|---|---|---|---|
| GPU requirement | Optional — runs fine CPU-only | Optional — runs fine CPU-only | Effectively requires a CUDA GPU for its throughput benefits; CPU support is not its design target |
| Fit for 16GB CPU-only box | Good — thin wrapper over llama.cpp with model management, REST API, streaming | Good, but you own model management, server, and API yourself | Poor — designed for high-throughput GPU serving with continuous batching; wasted/unsupported on this hardware |
| Ops simplicity | `docker run` + `ollama pull`, REST/streaming API out of the box | Requires building a server layer yourself | Heaviest to operate, GPU driver/CUDA dependency |
| Model swapping | `ollama pull <model>` + config change | Manual GGUF management | Manual, GPU-memory-constrained |

**Recommendation: Ollama.** It's llama.cpp under the hood (so no performance
penalty on CPU) but adds model pulling, a REST + streaming API, and simple
Docker packaging — exactly what's needed for Phase 2's `/chat` endpoint
without building a serving layer from scratch. vLLM is not viable at all on
this hardware (no GPU). This matches the stack already specified.

---

## 5. Recommended default stack

| Component | Default | Config key |
|---|---|---|
| LLM | Qwen2.5-7B-Instruct, Q4_K_M | `LLM_MODEL=qwen2.5:7b-instruct-q4_K_M` |
| Embeddings | BAAI/bge-small-en-v1.5 | `EMBEDDING_MODEL=BAAI/bge-small-en-v1.5` |
| Vector DB | Qdrant | `VECTOR_DB=qdrant` |
| Inference runtime | Ollama | `LLM_RUNTIME=ollama` |
| Chunk size / overlap (starting point, tune in Phase 9) | 500 tokens / 75 overlap | `CHUNK_SIZE=500`, `CHUNK_OVERLAP=75` |
| Relevance threshold (starting point, tune in Phase 9) | cosine 0.5 | `RELEVANCE_THRESHOLD=0.5` |

Revised from the original 0.35 guess after actually measuring bge-small-en-v1.5
on real data in Phase 4/5: unrelated query/passage pairs scored ~0.30-0.35,
related ones ~0.70-0.77. 0.5 sits cleanly in the gap between them; still
worth re-tuning once more real company documents are indexed (Phase 9).

### Hardware headroom check (16GB RAM, CPU-only)

- OS + misc: ~1.5 GB
- MongoDB: ~0.5-1 GB
- Qdrant: ~0.5-1 GB (grows with corpus size)
- Embedding model resident + batch buffers: ~0.5 GB
- Ollama + Qwen2.5-7B Q4_K_M loaded + KV cache: ~6-7 GB
- FastAPI app + OS buffers/cache: ~1-2 GB
- **Total: ~10-13 GB**, leaving ~3-6 GB headroom for concurrent requests and
  ingestion spikes (OCR, batch embedding). This is workable but not generous —
  avoid running ingestion and heavy chat traffic at the same time in
  production, and revisit if concurrent user count grows.

---

## Retrieval hit-rate eval script

See [`/eval/scripts/retrieval_hitrate.py`](../eval/scripts/retrieval_hitrate.py).
It loads 20 sample questions (`/eval/dataset/questions.jsonl`) each mapped to
an expected passage id in a small corpus (`/eval/dataset/corpus.jsonl`),
embeds both with each candidate embedding model, and reports hit-rate@1,
hit-rate@3, and hit-rate@5, plus mean embedding latency — so the choice above
can be re-validated once real company documents replace this placeholder
corpus (Phase 6).

Run it with:

```bash
cd eval
pip install -r requirements.txt
python scripts/retrieval_hitrate.py
```
