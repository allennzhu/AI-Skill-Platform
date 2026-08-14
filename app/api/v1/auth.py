from fastapi import Request

from app.api.errors import AppError
from app.biz.resolve import resolve_user_llm, resolve_user_llm_by_user_id
from app.config import Settings, get_settings
from app.llm.credentials import ResolvedLLM
from app.models.api import AgentResponse
from app.runtime.service import RuntimeService


def auth_failure_response(runtime: RuntimeService, session_id: str | None, status: str, message: str) -> AgentResponse:
    session = runtime.sessions.create(session_id)
    return AgentResponse(
        session_id=session.session_id,
        status=status,
        reply=message,
    )


def bearer_token(request: Request) -> str | None:
    auth = request.headers.get("Authorization") or ""
    if not auth.lower().startswith("bearer "):
        return None
    token = auth.split(" ", 1)[1].strip()
    return token or None


def internal_user_id(request: Request, settings: Settings) -> int | None:
    secret = (request.headers.get("X-Internal-Secret") or "").strip()
    raw_uid = (request.headers.get("X-Internal-User-Id") or "").strip()
    if not secret or not raw_uid:
        return None
    if not settings.biz_internal_secret or secret != settings.biz_internal_secret:
        return None
    try:
        user_id = int(raw_uid)
    except ValueError:
        return None
    return user_id if user_id > 0 else None


def resolve_request_llm(
    request: Request,
    runtime: RuntimeService,
    session_id: str | None,
) -> tuple[ResolvedLLM | None, AgentResponse | None]:
    settings = get_settings()
    token = bearer_token(request)
    uid = internal_user_id(request, settings)
    if not token and uid is None:
        return None, auth_failure_response(runtime, session_id, "unauthorized", "Authorization Bearer token required")
    try:
        if uid is not None:
            return resolve_user_llm_by_user_id(uid, settings), None
        return resolve_user_llm(token, settings), None
    except AppError as exc:
        if exc.code in ("unauthorized", "no_api_key", "llm_error"):
            return None, auth_failure_response(runtime, session_id, exc.code, exc.message)
        raise
