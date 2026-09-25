"""
Compares embedding models on retrieval hit-rate using a small fixed corpus.

Loads eval/dataset/corpus.jsonl (candidate passages) and
eval/dataset/questions.jsonl (question -> expected_passage_id), embeds both
with each candidate model, ranks corpus passages by cosine similarity to each
question, and reports hit-rate@1 / @3 / @5 plus mean embedding latency.

This is a placeholder-corpus sanity check for Phase 1's model choice. Re-run
it against real company documents in Phase 6 to confirm the choice still
holds.

Usage:
    cd eval
    pip install -r requirements.txt
    python scripts/retrieval_hitrate.py
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

DATASET_DIR = Path(__file__).resolve().parent.parent / "dataset"
CORPUS_PATH = DATASET_DIR / "corpus.jsonl"
QUESTIONS_PATH = DATASET_DIR / "questions.jsonl"

K_VALUES = (1, 3, 5)


@dataclass(frozen=True)
class ModelConfig:
    name: str
    query_prefix: str = ""
    passage_prefix: str = ""


MODELS = [
    ModelConfig(name="BAAI/bge-small-en-v1.5", query_prefix="Represent this sentence for searching relevant passages: "),
    ModelConfig(name="intfloat/e5-small-v2", query_prefix="query: ", passage_prefix="passage: "),
    ModelConfig(name="sentence-transformers/all-MiniLM-L6-v2"),
]


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def cosine_sim_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a_norm = a / np.linalg.norm(a, axis=1, keepdims=True)
    b_norm = b / np.linalg.norm(b, axis=1, keepdims=True)
    return a_norm @ b_norm.T


def hit_rate_at_k(ranked_ids: list[list[str]], expected_ids: list[str], k: int) -> float:
    hits = sum(1 for ranked, expected in zip(ranked_ids, expected_ids) if expected in ranked[:k])
    return hits / len(expected_ids)


def evaluate_model(config: ModelConfig, corpus: list[dict], questions: list[dict]) -> dict:
    model = SentenceTransformer(config.name)

    passage_texts = [config.passage_prefix + p["text"] for p in corpus]
    passage_ids = [p["id"] for p in corpus]

    query_texts = [config.query_prefix + q["question"] for q in questions]
    expected_ids = [q["expected_passage_id"] for q in questions]

    start = time.perf_counter()
    passage_embeddings = model.encode(passage_texts, convert_to_numpy=True, normalize_embeddings=False)
    query_embeddings = model.encode(query_texts, convert_to_numpy=True, normalize_embeddings=False)
    elapsed = time.perf_counter() - start
    mean_latency_ms = (elapsed / (len(passage_texts) + len(query_texts))) * 1000

    sims = cosine_sim_matrix(query_embeddings, passage_embeddings)
    ranked_ids = [
        [passage_ids[i] for i in row.argsort()[::-1]]
        for row in sims
    ]

    return {
        "model": config.name,
        "dimensions": passage_embeddings.shape[1],
        "mean_embed_latency_ms": round(mean_latency_ms, 2),
        **{f"hit_rate@{k}": round(hit_rate_at_k(ranked_ids, expected_ids, k), 3) for k in K_VALUES},
    }


def main() -> None:
    corpus = load_jsonl(CORPUS_PATH)
    questions = load_jsonl(QUESTIONS_PATH)

    print(f"Corpus: {len(corpus)} passages | Questions: {len(questions)}\n")

    results = []
    for config in MODELS:
        print(f"Evaluating {config.name} ...")
        results.append(evaluate_model(config, corpus, questions))

    header = f"{'Model':<40} {'Dim':>5} {'Latency(ms)':>12} " + " ".join(f"HR@{k:<4}" for k in K_VALUES)
    print("\n" + header)
    print("-" * len(header))
    for r in results:
        row = f"{r['model']:<40} {r['dimensions']:>5} {r['mean_embed_latency_ms']:>12} "
        row += " ".join(f"{r[f'hit_rate@{k}']:<6}" for k in K_VALUES)
        print(row)


if __name__ == "__main__":
    main()
