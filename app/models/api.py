from typing import Any, Optional
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    today: Optional[str] = None

class RouteRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    today: Optional[str] = None

class ExecuteRequest(BaseModel):
    intent: str
    slots: dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None

class AgentResponse(BaseModel):
    session_id: str
    status: str
    intent: Optional[str] = None
    slots: dict[str, Any] = Field(default_factory=dict)
    missing_slots: list[str] = Field(default_factory=list)
    result: Optional[dict[str, Any]] = None
    reply: Optional[str] = None
