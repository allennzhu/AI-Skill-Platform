from fastapi import Request

from app.runtime.service import RuntimeService


def get_runtime(request: Request) -> RuntimeService:
    return request.app.state.runtime
