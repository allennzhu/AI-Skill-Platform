from fastapi import APIRouter, Depends

from app.api.deps import get_runtime
from app.api.errors import AppError
from app.models.api import AgentResponse, ExecuteRequest
from app.runtime.service import RuntimeService

router = APIRouter()


@router.post("/v1/execute", response_model=AgentResponse)
def execute(body: ExecuteRequest, runtime: RuntimeService = Depends(get_runtime)):
    if not body.intent:
        raise AppError(code="bad_request", message="intent is required")
    result = runtime.run(body.intent, body.slots, body.session_id)
    return AgentResponse(**result.__dict__)
