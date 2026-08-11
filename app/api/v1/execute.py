from fastapi import APIRouter, Depends, Request

from app.api.deps import get_runtime
from app.api.errors import AppError
from app.biz.resolve import resolve_user_llm
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


@router.post("/v1/execute", response_model=AgentResponse)
def execute(
    body: ExecuteRequest,
    request: Request,
    runtime: RuntimeService = Depends(get_runtime),
):
    if not body.intent:
        raise AppError(code="bad_request", message="intent is required")

    token = _bearer_token(request)
    if not token:
        return _auth_failure_response(runtime, body.session_id, "unauthorized", "Authorization Bearer token required")

    try:
        resolved = resolve_user_llm(token, get_settings())
    except AppError as exc:
        if exc.code in ("unauthorized", "no_api_key", "llm_error"):
            return _auth_failure_response(runtime, body.session_id, exc.code, exc.message)
        raise

    ctx_token = set_request_llm(resolved)
    try:
        result = runtime.run(body.intent, body.slots, body.session_id)
        return AgentResponse(**result.__dict__)
    finally:
        reset_request_llm(ctx_token)
