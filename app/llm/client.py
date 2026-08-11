from collections.abc import Callable
from typing import Protocol

import httpx

from app.api.errors import AppError
from app.config import Settings

import logging

logger = logging.getLogger(__name__)


class LLMClient(Protocol):
    def complete(self, system: str, user: str) -> str: ...


class HttpLLMClient:
    def __init__(
        self,
        settings: Settings,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
    ):
        self.settings = settings
        self.base_url = (base_url or settings.llm_base_url).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.llm_api_key
        self.model = model if model is not None else settings.llm_model
        self.timeout = timeout if timeout is not None else settings.llm_timeout_seconds

    def complete(self, system: str, user: str) -> str:
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise TypeError("LLM content must be a string")
            return content
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            logger.error(
                "LLM request failed: base_url=%s model=%s cause=%s: %s",
                self.base_url,
                self.model,
                type(exc).__name__,
                exc,
            )
            raise AppError(
                code="llm_error",
                message="LLM request failed",
                status_code=502,
            ) from exc


class FakeLLMClient:
    def __init__(self, scripted: str | Callable[[str, str], str]):
        self.scripted = scripted

    def complete(self, system: str, user: str) -> str:
        if callable(self.scripted):
            return self.scripted(system, user)
        return self.scripted
