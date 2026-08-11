from __future__ import annotations

import httpx

from app.api.errors import AppError
from app.config import Settings
from app.llm.credentials import ResolvedLLM


def resolve_user_llm(token: str, settings: Settings) -> ResolvedLLM:
    if not token or not token.strip():
        raise AppError(code="unauthorized", message="Missing oauth token", status_code=401)
    if not settings.biz_base_url or not settings.biz_internal_secret:
        raise AppError(
            code="llm_error",
            message="Biz resolve is not configured",
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
            json={"oauth_token": token},
            timeout=settings.biz_resolve_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise AppError(
            code="llm_error",
            message="Biz resolve request failed",
            status_code=502,
        ) from exc

    try:
        body = response.json()
    except ValueError as exc:
        raise AppError(
            code="llm_error",
            message="Biz resolve returned invalid JSON",
            status_code=502,
        ) from exc

    code = body.get("code")
    if response.status_code == 403 or code == 403:
        raise AppError(code="llm_error", message="Biz resolve forbidden", status_code=502)
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
