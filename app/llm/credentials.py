from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass

from app.api.errors import AppError
from app.config import get_settings
from app.llm.client import HttpLLMClient, LLMClient


@dataclass(frozen=True)
class ResolvedLLM:
    base_url: str
    api_key: str
    model: str


_llm_ctx: ContextVar[ResolvedLLM | None] = ContextVar("request_llm", default=None)


def set_request_llm(resolved: ResolvedLLM) -> Token:
    return _llm_ctx.set(resolved)


def reset_request_llm(token: Token) -> None:
    _llm_ctx.reset(token)


def get_request_llm_client(*, timeout: float | None = None) -> LLMClient:
    creds = _llm_ctx.get()
    if creds is None:
        raise AppError(
            code="unauthorized",
            message="Missing LLM credentials",
            status_code=401,
        )
    return HttpLLMClient(
        get_settings(),
        base_url=creds.base_url,
        api_key=creds.api_key,
        model=creds.model,
        timeout=timeout,
    )
