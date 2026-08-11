from collections.abc import Callable
from typing import Protocol
import logging
import time

import httpx

from app.api.errors import AppError
from app.config import Settings

logger = logging.getLogger(__name__)

# 免费/冷启动网关常见瞬时失败：524 Origin Timeout、502/503/429 等
_RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504, 520, 522, 524}


class LLMClient(Protocol):
    def complete(self, system: str, user: str) -> str: ...


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError)):
        return True
    if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
        return exc.response.status_code in _RETRYABLE_STATUS
    return False


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
        self.retry_times = max(0, int(getattr(settings, "llm_retry_times", 1)))
        self.retry_backoff_seconds = float(getattr(settings, "llm_retry_backoff_seconds", 1.0))

    def complete(self, system: str, user: str) -> str:
        attempts = self.retry_times + 1
        last_exc: BaseException | None = None
        for attempt in range(1, attempts + 1):
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
                last_exc = exc
                if attempt < attempts and _is_retryable(exc):
                    logger.warning(
                        "LLM request retryable failure (attempt %s/%s): base_url=%s model=%s cause=%s: %s",
                        attempt,
                        attempts,
                        self.base_url,
                        self.model,
                        type(exc).__name__,
                        exc,
                    )
                    time.sleep(self.retry_backoff_seconds)
                    continue
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
        raise AppError(
            code="llm_error",
            message="LLM request failed",
            status_code=502,
        ) from last_exc


class FakeLLMClient:
    def __init__(self, scripted: str | Callable[[str, str], str]):
        self.scripted = scripted

    def complete(self, system: str, user: str) -> str:
        if callable(self.scripted):
            return self.scripted(system, user)
        return self.scripted
