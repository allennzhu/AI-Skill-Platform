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


class _ProviderResponseError(Exception):
    """OpenAI 兼容接口 HTTP 200，但 body 是 error、没有 choices。"""

    def __init__(self, message: str, code: int | None = None):
        self.provider_code = code
        super().__init__(message)


def _as_int_code(value: object) -> int | None:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _stringify_chat_content(content: object) -> str:
    """兼容 OpenAI 字符串，以及 OpenRouter/Claude 的 content 数组。"""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        raise TypeError("LLM content must be a string")
    texts: list[str] = []
    fallback: list[str] = []
    for item in content:
        if isinstance(item, str):
            fallback.append(item)
            continue
        if not isinstance(item, dict):
            continue
        text = item.get("text")
        if not isinstance(text, str) or text == "":
            continue
        kind = str(item.get("type") or "text").lower()
        if kind in {"text", "output_text"}:
            texts.append(text)
        else:
            fallback.append(text)
    joined = "".join(texts) if texts else "".join(fallback)
    if not joined:
        raise TypeError("LLM content must be a string")
    return joined


def _extract_chat_content(payload: object) -> str:
    if not isinstance(payload, dict):
        raise ValueError("模型返回不是 JSON 对象")
    err = payload.get("error")
    if err:
        if isinstance(err, dict):
            msg = str(err.get("message") or err.get("msg") or err).strip()
            code = _as_int_code(err.get("code") or err.get("status"))
        else:
            msg = str(err).strip()
            code = None
        raise _ProviderResponseError(msg or "模型服务返回错误", code)
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("模型返回缺少 choices（免费模型常无可用渠道，请换模型后重试）")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    if not isinstance(message, dict):
        raise ValueError("模型返回缺少 message")
    return _stringify_chat_content(message.get("content"))


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError)):
        return True
    if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
        return exc.response.status_code in _RETRYABLE_STATUS
    if isinstance(exc, _ProviderResponseError) and exc.provider_code in _RETRYABLE_STATUS:
        return True
    return False


def _friendly_llm_message(exc: BaseException) -> str:
    if isinstance(exc, _ProviderResponseError):
        text = str(exc).strip()
        if exc.provider_code == 429:
            return f"模型服务请求过于频繁（429）：{text}"
        if exc.provider_code:
            return f"模型服务返回错误（{exc.provider_code}）：{text}"
        return f"模型服务返回错误：{text}"
    if isinstance(exc, httpx.TimeoutException):
        return "调用模型超时，请稍后重试"
    if isinstance(exc, (httpx.ConnectError, httpx.RemoteProtocolError)):
        return "无法连接模型服务，请检查 Base URL 或网络"
    if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
        code = exc.response.status_code
        if code == 401:
            return "模型没通过验证（401）。请到 51PM「我的工作台」→「51PM Agent配置」检查 API Key 和默认模型；还没添加就点「+ 新增 API Key」。"
        if code == 403:
            return "模型服务禁止访问（403），请检查 Key 权限或余额"
        if code == 404:
            return "模型不存在（404），请检查默认模型名称"
        if code == 429:
            return "模型服务请求过于频繁（429），请稍后再试或更换模型"
        if code in (408, 500, 502, 503, 504, 520, 522, 524):
            return f"模型服务暂时不可用（{code}），请稍后重试"
        return f"模型服务返回错误（HTTP {code}）"
    if isinstance(exc, (KeyError, IndexError, ValueError, TypeError)):
        return "模型返回格式异常（免费模型常无可用渠道），请更换模型后重试"
    return "模型调用失败，请稍后重试"


class HttpLLMClient:
    def __init__(
        self,
        settings: Settings,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout if timeout is not None else settings.llm_timeout_seconds
        self.retry_times = max(0, int(settings.llm_retry_times))
        self.retry_backoff_seconds = float(settings.llm_retry_backoff_seconds)

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
                return _extract_chat_content(response.json())
            except (httpx.HTTPError, _ProviderResponseError, KeyError, IndexError, TypeError, ValueError) as exc:
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
                    message=_friendly_llm_message(exc),
                    status_code=502,
                ) from exc
        raise AppError(
            code="llm_error",
            message=_friendly_llm_message(last_exc) if last_exc else "模型调用失败，请稍后重试",
            status_code=502,
        ) from last_exc


class FakeLLMClient:
    def __init__(self, scripted: str | Callable[[str, str], str]):
        self.scripted = scripted

    def complete(self, system: str, user: str) -> str:
        if callable(self.scripted):
            return self.scripted(system, user)
        return self.scripted
