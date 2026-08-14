from fastapi import APIRouter, Depends, Request

from app.api.deps import get_runtime
from app.api.errors import AppError
from app.biz.resolve import resolve_user_llm, resolve_user_llm_by_user_id
from app.config import get_settings
from app.llm.credentials import reset_request_llm, set_request_llm
from app.models.api import AgentResponse, ExecuteRequest
from app.runtime.service import RuntimeService

router = APIRouter()


def _auth_failure_response(runtime: RuntimeService, session_id: str | None, status: str, message: str) -> AgentResponse:
    session = runtime.sessions.create(session_id)
    return AgentResponse(
        session_id=session.session_id,
        status=status,
        reply=message,
    )


def _bearer_token(request: Request) -> str | None:
    auth = request.headers.get("Authorization") or ""
    if not auth.lower().startswith("bearer "):
        return None
    token = auth.split(" ", 1)[1].strip()
    return token or None


def _internal_user_id(request: Request, settings) -> int | None:
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


@router.post("/v1/execute", response_model=AgentResponse)
def execute(
    body: ExecuteRequest,
    request: Request,
    runtime: RuntimeService = Depends(get_runtime),
):
    if not body.intent:
        raise AppError(code="bad_request", message="intent is required")

    settings = get_settings()
    token = _bearer_token(request)
    internal_uid = _internal_user_id(request, settings)
    if not token and internal_uid is None:
        return _auth_failure_response(runtime, body.session_id, "unauthorized", "Authorization Bearer token required")

    try:
        if internal_uid is not None:
            resolved = resolve_user_llm_by_user_id(internal_uid, settings)
        else:
            resolved = resolve_user_llm(token, settings)
    except AppError as exc:
        if exc.code in ("unauthorized", "no_api_key", "llm_error"):
            return _auth_failure_response(runtime, body.session_id, exc.code, exc.message)
        raise

    ctx_token = set_request_llm(resolved)
    try:
        result = runtime.run(body.intent, body.slots, body.session_id)
        return AgentResponse(**result.__dict__)
    except AppError as exc:
        if exc.code in ("unauthorized", "no_api_key", "llm_error"):
            return _auth_failure_response(runtime, body.session_id, exc.code, exc.message)
        raise
    finally:
        reset_request_llm(ctx_token)
