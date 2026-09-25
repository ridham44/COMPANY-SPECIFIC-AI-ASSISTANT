from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import chat, health
from app.core.config import get_settings
from app.services.llm_client import OllamaLLMClient


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.llm_client = OllamaLLMClient(settings)
    try:
        yield
    finally:
        await app.state.llm_client.aclose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.include_router(health.router)
    app.include_router(chat.router)
    return app


app = create_app()
