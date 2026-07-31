from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass
class RuntimeResult:
    session_id: str
    status: str
    intent: Optional[str] = None
    slots: dict[str, Any] = field(default_factory=dict)
    missing_slots: list[str] = field(default_factory=list)
    result: Optional[dict[str, Any]] = None
    reply: Optional[str] = None
