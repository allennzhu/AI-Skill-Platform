from fastapi import FastAPI
from app.api.v1 import health as health_api

def create_app() -> FastAPI:
    app = FastAPI(title="AI Skill Platform")
    app.include_router(health_api.router)
    return app

app = create_app()
