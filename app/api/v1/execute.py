from fastapi import APIRouter, Depends, Request

from app.api.deps import get_runtime
from app.api.errors import AppError
from app.api.v1.auth import auth_failure_response, bearer_token, internal_user_id
from app.biz.resolve import resolve_user_llm, resolve_user_llm_by_user_id
from app.config import get_settings
from app.llm.credentials import reset_request_llm, set_request_llm
from app.models.api import AgentResponse, ExecuteRequest
from app.runtime.service import RuntimeService


router = APIRouter()


@router.post("/v1/execute", response_model=AgentResponse)
def execute(
    body: ExecuteRequest,
    request: Request,
    runtime: RuntimeService = Depends(get_runtime),
):
    if not body.intent:
        raise AppError(code="bad_request", message="intent is required")

    settings = get_settings()
    token = bearer_token(request)
    uid = internal_user_id(request, settings)
    if not token and uid is None:
        return auth_failure_response(runtime, body.session_id, "unauthorized", "Authorization Bearer token required")

    try:
        if uid is not None:
            resolved = resolve_user_llm_by_user_id(uid, settings)
        else:
            resolved = resolve_user_llm(token, settings)
    except AppError as exc:
        if exc.code in ("unauthorized", "no_api_key", "llm_error"):
            return auth_failure_response(runtime, body.session_id, exc.code, exc.message)
        raise

    ctx_token = set_request_llm(resolved)
    try:
        result = runtime.run(body.intent, body.slots, body.session_id)
        return AgentResponse(**result.__dict__)
    except AppError as exc:
        if exc.code in ("unauthorized", "no_api_key", "llm_error"):
            return auth_failure_response(runtime, body.session_id, exc.code, exc.message)
        raise
    finally:
        reset_request_llm(ctx_token)
