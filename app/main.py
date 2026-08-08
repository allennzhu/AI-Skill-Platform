from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_exception_handlers
from app.api.v1 import chat as chat_api
from app.api.v1 import execute as execute_api
from app.api.v1 import health as health_api
from app.config import get_settings
from app.conversation.controller import ConversationController
from app.llm.client import HttpLLMClient, LLMClient
from app.runtime.registry import SkillRegistry
from app.runtime.service import RuntimeService
from app.runtime.session import SessionStore


def create_app(llm_client: LLMClient | None = None) -> FastAPI:
    settings = get_settings()
    skills_root = Path(__file__).resolve().parent / "skills"
    app = FastAPI(title="AI Skill Platform")
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    cors_kwargs: dict = dict(
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    if settings.cors_origin_regex:
        cors_kwargs["allow_origin_regex"] = settings.cors_origin_regex
    app.add_middleware(CORSMiddleware, **cors_kwargs)
    app.state.settings = settings
    app.state.runtime = RuntimeService(
        registry=SkillRegistry.load_dir(skills_root),
        sessions=SessionStore(ttl_seconds=settings.session_ttl_seconds),
    )
    app.state.llm_client = llm_client or HttpLLMClient(settings)
    app.state.conversation = ConversationController(
        app.state.runtime,
        app.state.llm_client,
    )
    register_exception_handlers(app)
    app.include_router(health_api.router)
    app.include_router(execute_api.router)
    app.include_router(chat_api.router)
    return app

app = create_app()
