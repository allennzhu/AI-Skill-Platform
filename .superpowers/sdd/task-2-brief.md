### Task 2: API 模型与错误处理

**Files:**
- Create: `E:\AI-Skill-Platform\app\models\__init__.py`
- Create: `E:\AI-Skill-Platform\app\models\api.py`
- Create: `E:\AI-Skill-Platform\app\models\runtime.py`
- Create: `E:\AI-Skill-Platform\app\api\errors.py`
- Modify: `E:\AI-Skill-Platform\app\main.py`
- Create: `E:\AI-Skill-Platform\tests\test_errors.py`

**Interfaces:**
- Consumes: `create_app`
- Produces:
  - `ChatRequest(message: str, session_id: str | None = None)`
  - `ExecuteRequest(intent: str, slots: dict[str, Any] = {}, session_id: str | None = None)`
  - `AgentResponse` 字段：`session_id`, `status`, `intent`, `slots`, `missing_slots`, `result`, `reply`（可选字段用默认 None）
  - `AppError(code: str, message: str, details: dict | None = None, status_code: int = 400)`
  - `RuntimeResult` dataclass：同上业务字段（供 Runtime 返回）

- [ ] **Step 1: 写失败测试**

`tests/test_errors.py`:
```python
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.errors import AppError, register_exception_handlers

def test_app_error_shape():
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom")
    def boom():
        raise AppError(code="bad_request", message="missing field", details={"field": "message"})

    r = TestClient(app).get("/boom")
    assert r.status_code == 400
    body = r.json()
    assert body["error"]["code"] == "bad_request"
    assert body["error"]["message"] == "missing field"
    assert body["error"]["details"]["field"] == "message"
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest tests/test_errors.py -v`  
Expected: FAIL（模块不存在）

- [ ] **Step 3: 实现模型与 handler**

`app/models/api.py`:
```python
from typing import Any, Optional
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

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
```

`app/models/runtime.py`:
```python
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
```

`app/api/errors.py`:
```python
from typing import Any, Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

class AppError(Exception):
    def __init__(self, code: str, message: str, details: Optional[dict[str, Any]] = None, status_code: int = 400):
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
        )
```

在 `create_app()` 中调用 `register_exception_handlers(app)`。

- [ ] **Step 4: 测试通过**

Run: `pytest tests/test_errors.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/models app/api/errors.py app/main.py tests/test_errors.py
git commit -m "feat: add API models and AppError handler"
```

---

