from fastapi import Request

from app.conversation.controller import ConversationController
from app.runtime.service import RuntimeService


def get_runtime(request: Request) -> RuntimeService:
    return request.app.state.runtime


def get_conversation_controller(request: Request) -> ConversationController:
    return request.app.state.conversation
