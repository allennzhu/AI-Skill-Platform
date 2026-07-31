from collections.abc import Callable
from typing import Protocol

import httpx

from app.api.errors import AppError
from app.config import Settings


class LLMClient(Protocol):
    def complete(self, system: str, user: str) -> str: ...


class HttpLLMClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def complete(self, system: str, user: str) -> str:
        try:
            response = httpx.post(
                f"{self.settings.llm_base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {self.settings.llm_api_key}"},
                json={
                    "model": self.settings.llm_model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0,
                },
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise TypeError("LLM content must be a string")
            return content
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
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
