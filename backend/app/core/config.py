from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Company Knowledge Assistant"
    environment: str = "development"

    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "qwen2.5:7b-instruct-q4_K_M"
    llm_temperature: float = 0.2
    llm_request_timeout_seconds: float = 120.0

    embedding_model: str = "BAAI/bge-small-en-v1.5"

    retrieval_top_k: int = 5
    relevance_score_threshold: float = 0.35
    chunk_size: int = 500
    chunk_overlap: int = 75
    no_answer_reply: str = "I don't have enough information in the company knowledge base to answer this question."

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "company_assistant"

    qdrant_url: str = "http://localhost:6333"


@lru_cache
def get_settings() -> Settings:
    return Settings()
