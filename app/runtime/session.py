from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SessionData:
    session_id: str
    intent: Optional[str] = None
    slots: dict[str, Any] = field(default_factory=dict)
    updated_at: float = field(default_factory=time.time)


class SessionStore:
    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self._data: dict[str, SessionData] = {}

    def create(self, session_id: Optional[str] = None) -> SessionData:
        sid = session_id or str(uuid.uuid4())
        data = SessionData(session_id=sid)
        self._data[sid] = data
        return data

    def get(self, session_id: str) -> Optional[SessionData]:
        data = self._data.get(session_id)
        if data is None:
            return None
        if time.time() - data.updated_at > self.ttl_seconds:
            self._data.pop(session_id, None)
            return None
        return data

    def save(self, data: SessionData) -> None:
        self._data[data.session_id] = data

    def merge_slots(
        self, data: SessionData, intent: Optional[str], slots: dict[str, Any]
    ) -> SessionData:
        if intent:
            if data.intent and data.intent != intent:
                data.slots = {}
            data.intent = intent
        data.slots.update(slots or {})
        data.updated_at = time.time()
        return data
