### Task 3: 内存 Session

**Files:**
- Create: `E:\AI-Skill-Platform\app\runtime\__init__.py`
- Create: `E:\AI-Skill-Platform\app\runtime\session.py`
- Create: `E:\AI-Skill-Platform\tests\test_session.py`

**Interfaces:**
- Consumes: `Settings.session_ttl_seconds`
- Produces:
  - `SessionData(session_id, intent: str | None, slots: dict, updated_at: float)`
  - `SessionStore(ttl_seconds: int)`
  - `create(session_id: str | None = None) -> SessionData`
  - `get(session_id: str) -> SessionData | None`（过期返回 None 并删除）
  - `save(data: SessionData) -> None`
  - `merge_slots(data: SessionData, intent: str | None, slots: dict) -> SessionData`

- [ ] **Step 1: 写失败测试**

`tests/test_session.py`:
```python
import time
from app.runtime.session import SessionStore

def test_create_and_merge_slots():
    store = SessionStore(ttl_seconds=60)
    s = store.create()
    assert s.session_id
    s = store.merge_slots(s, intent="echo", slots={"text": "a"})
    s = store.merge_slots(s, intent="echo", slots={"text": "b", "extra": 1})
    assert s.slots == {"text": "b", "extra": 1}
    assert s.intent == "echo"
    store.save(s)
    loaded = store.get(s.session_id)
    assert loaded is not None
    assert loaded.slots["text"] == "b"

def test_expired_session_returns_none():
    store = SessionStore(ttl_seconds=1)
    s = store.create()
    store.save(s)
    s.updated_at = time.time() - 10
    store.save(s)
    assert store.get(s.session_id) is None
```

- [ ] **Step 2: 运行确认失败** → Expected: FAIL

- [ ] **Step 3: 实现**

`app/runtime/session.py`:
```python
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
        data.updated_at = time.time()
        self._data[data.session_id] = data

    def merge_slots(self, data: SessionData, intent: Optional[str], slots: dict[str, Any]) -> SessionData:
        if intent:
            data.intent = intent
        data.slots.update(slots or {})
        data.updated_at = time.time()
        return data
```

- [ ] **Step 4: 测试通过** → `pytest tests/test_session.py -v`

- [ ] **Step 5: Commit** → `feat: add in-memory session store`

---

