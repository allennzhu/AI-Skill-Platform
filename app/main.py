from pathlib import Path

from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.v1 import chat as chat_api
from app.api.v1 import execute as execute_api
from app.api.v1 import health as health_api
from app.api.v1 import route as route_api
from app.config import get_settings
from app.conversation.controller import ConversationController
from app.llm.client import LLMClient
from app.runtime.registry import SkillRegistry
from app.runtime.service import RuntimeService
from app.runtime.session import SessionStore


def create_app(llm_client: LLMClient | None = None) -> FastAPI:
    settings = get_settings()
    skills_root = Path(__file__).resolve().parent / "skills"
    app = FastAPI(title="AI Skill Platform")
    app.state.settings = settings
    app.state.runtime = RuntimeService(
        registry=SkillRegistry.load_dir(skills_root),
        sessions=SessionStore(ttl_seconds=settings.session_ttl_seconds),
    )
    app.state.conversation = ConversationController(
        app.state.runtime,
        llm_client,
    )
    register_exception_handlers(app)
    app.include_router(health_api.router)
    app.include_router(execute_api.router)
    app.include_router(chat_api.router)
    app.include_router(route_api.router)
    return app


app = create_app()
