from __future__ import annotations

import logging

import httpx

from app.api.errors import AppError
from app.config import Settings
from app.llm.credentials import ResolvedLLM

logger = logging.getLogger(__name__)


def _resolve_connect_message(base_url: str, exc: BaseException) -> str:
    if isinstance(exc, httpx.TimeoutException):
        return f"连接 51PM 解析接口超时（{base_url}），请检查正式环境网络或加大 BIZ_RESOLVE_TIMEOUT_SECONDS"
    if isinstance(exc, httpx.ConnectError):
        return f"无法连接 51PM 解析接口（{base_url}），请把 Agent 的 BIZ_BASE_URL 改成正式环境 51PM 地址（同机可用 http://127.0.0.1:8888）"
    return f"无法请求 51PM 解析接口（{base_url}）：{type(exc).__name__}"


def _post_resolve(settings: Settings, payload: dict) -> ResolvedLLM:
    if not settings.biz_base_url or not settings.biz_internal_secret:
        raise AppError(
            code="llm_error",
            message="Agent 未配置 BIZ_BASE_URL / BIZ_INTERNAL_SECRET",
            status_code=502,
        )
    url = f"{settings.biz_base_url.rstrip('/')}/internal_api/ai_api_key/resolve"
    try:
        response = httpx.post(
            url,
            headers={
                "X-Internal-Secret": settings.biz_internal_secret,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=settings.biz_resolve_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        logger.error("Biz resolve request failed: url=%s cause=%s: %s", url, type(exc).__name__, exc)
        raise AppError(
            code="llm_error",
            message=_resolve_connect_message(settings.biz_base_url, exc),
            status_code=502,
        ) from exc

    try:
        body = response.json()
    except ValueError as exc:
        raise AppError(
            code="llm_error",
            message=f"51PM 解析接口返回了非 JSON（{settings.biz_base_url}），请确认正式环境已发布 internal_api 且 Nginx 未拦截该路径",
            status_code=502,
        ) from exc

    code = body.get("code")
    if response.status_code == 403 or code == 403:
        raise AppError(
            code="llm_error",
            message="51PM 拒绝解析（403），请确认正式环境 aiApiKey.internalSecret 与 Agent 的 BIZ_INTERNAL_SECRET 一致",
            status_code=502,
        )
    if code == 401:
        raise AppError(code="unauthorized", message="invalid_token", status_code=401)
    if code == 404:
        raise AppError(code="no_api_key", message="not_configured", status_code=404)
    if code != 0:
        raise AppError(
            code="llm_error",
            message=str(body.get("msg") or "Biz resolve failed"),
            status_code=502,
        )

    data = body.get("data") or {}
    base_url = (data.get("base_url") or "").strip()
    api_key = (data.get("api_key") or "").strip()
    model = (data.get("model") or "").strip()
    if not base_url or not api_key or not model:
        raise AppError(
            code="llm_error",
            message="Biz resolve returned incomplete credentials",
            status_code=502,
        )
    return ResolvedLLM(base_url=base_url, api_key=api_key, model=model)


def resolve_user_llm(token: str, settings: Settings) -> ResolvedLLM:
    if not token or not token.strip():
        raise AppError(code="unauthorized", message="Missing oauth token", status_code=401)
    return _post_resolve(settings, {"oauth_token": token})


def resolve_user_llm_by_user_id(user_id: int, settings: Settings) -> ResolvedLLM:
    if user_id <= 0:
        raise AppError(code="unauthorized", message="Missing user id", status_code=401)
    return _post_resolve(settings, {"user_id": user_id})
