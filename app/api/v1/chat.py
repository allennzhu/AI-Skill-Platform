from fastapi import APIRouter, Depends, Request

from app.api.deps import get_conversation_controller, get_runtime
from app.api.errors import AppError
from app.api.v1.execute import _auth_failure_response, _bearer_token
from app.biz.resolve import resolve_user_llm
from app.config import get_settings
from app.conversation.controller import ConversationController
from app.llm.credentials import reset_request_llm, set_request_llm
from app.models.api import AgentResponse, ChatRequest
from app.runtime.service import RuntimeService


router = APIRouter()


@router.post("/v1/chat", response_model=AgentResponse)
def chat(
    body: ChatRequest,
    request: Request,
    controller: ConversationController = Depends(get_conversation_controller),
    runtime: RuntimeService = Depends(get_runtime),
):
    token = _bearer_token(request)
    if not token:
        return _auth_failure_response(
            runtime, body.session_id, "unauthorized", "Authorization Bearer token required"
        )

    try:
        resolved = resolve_user_llm(token, get_settings())
    except AppError as exc:
        if exc.code in ("unauthorized", "no_api_key", "llm_error"):
            return _auth_failure_response(runtime, body.session_id, exc.code, exc.message)
        raise

    ctx_token = set_request_llm(resolved)
    try:
        result = controller.handle_chat(body.message, body.session_id)
        return AgentResponse(**result.__dict__)
    finally:
        reset_request_llm(ctx_token)
