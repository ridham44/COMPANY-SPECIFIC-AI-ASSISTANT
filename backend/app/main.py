from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import chat, conversations, documents, health
from app.core.config import get_settings
from app.db import init_db
from app.rag.pipeline import RagPipeline
from app.rag.retriever import Retriever
from app.services.embedding_service import SentenceTransformerEmbeddingService
from app.services.llm_client import OllamaLLMClient
from app.services.vector_store import QdrantVectorStore


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()

    app.state.mongo_client = await init_db(settings)
    app.state.embedding_service = SentenceTransformerEmbeddingService(settings)
    app.state.vector_store = QdrantVectorStore(settings)
    app.state.llm_client = OllamaLLMClient(settings)

    retriever = Retriever(
        embedding_service=app.state.embedding_service,
        vector_store=app.state.vector_store,
        top_k=settings.retrieval_top_k,
        score_threshold=settings.relevance_score_threshold,
    )
    app.state.rag_pipeline = RagPipeline(
        retriever=retriever,
        llm_client=app.state.llm_client,
        no_answer_reply=settings.no_answer_reply,
        llm_temperature=settings.llm_temperature,
    )

    try:
        yield
    finally:
        await app.state.llm_client.aclose()
        app.state.mongo_client.close()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(documents.router)
    app.include_router(conversations.router)
    return app


app = create_app()
