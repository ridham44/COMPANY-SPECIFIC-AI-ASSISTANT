from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

import httpx

from app.core.config import Settings


class LLMClient(ABC):
    @abstractmethod
    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
    ) -> AsyncIterator[str]:
        ...

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
    ) -> str:
        ...

    @abstractmethod
    async def aclose(self) -> None: ...


class OllamaLLMClient(LLMClient):
    def __init__(self, settings: Settings) -> None:
        self._model = settings.llm_model
        self._default_temperature = settings.llm_temperature
        self._client = httpx.AsyncClient(
            base_url=settings.ollama_base_url,
            timeout=settings.llm_request_timeout_seconds,
        )

    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
    ) -> AsyncIterator[str]:
        payload = {
            "model": self._model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": temperature if temperature is not None else self._default_temperature},
        }
        async with self._client.stream("POST", "/api/chat", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                chunk = json.loads(line)
                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield content
                if chunk.get("done"):
                    break

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
    ) -> str:
        parts = [part async for part in self.stream_chat(messages, temperature)]
        return "".join(parts)

    async def aclose(self) -> None:
        await self._client.aclose()
