from fastapi import APIRouter, Depends

from app.api.deps import get_conversation_controller
from app.conversation.controller import ConversationController
from app.models.api import AgentResponse, ChatRequest


router = APIRouter()


@router.post("/v1/chat", response_model=AgentResponse)
def chat(
    body: ChatRequest,
    controller: ConversationController = Depends(get_conversation_controller),
):
    result = controller.handle_chat(body.message, body.session_id)
    return AgentResponse(**result.__dict__)
