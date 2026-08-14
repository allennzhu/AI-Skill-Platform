from fastapi import APIRouter, Depends, Request

from app.api.deps import get_conversation_controller, get_runtime
from app.api.v1.auth import resolve_request_llm
from app.conversation.controller import ConversationController
from app.llm.credentials import reset_request_llm, set_request_llm
from app.models.api import AgentResponse, RouteRequest
from app.runtime.service import RuntimeService


router = APIRouter()


@router.post("/v1/route", response_model=AgentResponse)
def route(
    body: RouteRequest,
    request: Request,
    controller: ConversationController = Depends(get_conversation_controller),
    runtime: RuntimeService = Depends(get_runtime),
):
    resolved, err_res = resolve_request_llm(request, runtime, body.session_id)
    if err_res is not None:
        return err_res

    ctx_token = set_request_llm(resolved)
    try:
        result = controller.handle_route(body.message, body.session_id, body.today)
        return AgentResponse(**result.__dict__)
    finally:
        reset_request_llm(ctx_token)
