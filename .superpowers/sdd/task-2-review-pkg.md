# Review package: 7226dd25a961fb27b5b3a25b81c410ab25c16a49..622bc1b3aece849fed065d0a79dfd7eb0b701243
## Commits
622bc1b feat: add API models and AppError handler

## Files changed
 app/api/errors.py      | 19 +++++++++++++++++++
 app/main.py            |  2 ++
 app/models/__init__.py |  0
 app/models/api.py      | 20 ++++++++++++++++++++
 app/models/runtime.py  | 12 ++++++++++++
 tests/test_errors.py   | 18 ++++++++++++++++++
 6 files changed, 71 insertions(+)

## Diff
diff --git a/app/api/errors.py b/app/api/errors.py
new file mode 100644
index 0000000..c6e79f3
--- /dev/null
+++ b/app/api/errors.py
@@ -0,0 +1,19 @@
+from typing import Any, Optional
+from fastapi import FastAPI, Request
+from fastapi.responses import JSONResponse
+
+class AppError(Exception):
+    def __init__(self, code: str, message: str, details: Optional[dict[str, Any]] = None, status_code: int = 400):
+        self.code = code
+        self.message = message
+        self.details = details or {}
+        self.status_code = status_code
+        super().__init__(message)
+
+def register_exception_handlers(app: FastAPI) -> None:
+    @app.exception_handler(AppError)
+    async def app_error_handler(_: Request, exc: AppError):
+        return JSONResponse(
+            status_code=exc.status_code,
+            content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
+        )
diff --git a/app/main.py b/app/main.py
index 0c9cc6b..c380087 100644
--- a/app/main.py
+++ b/app/main.py
@@ -1,9 +1,11 @@
 from fastapi import FastAPI
+from app.api.errors import register_exception_handlers
 from app.api.v1 import health as health_api
 
 def create_app() -> FastAPI:
     app = FastAPI(title="AI Skill Platform")
+    register_exception_handlers(app)
     app.include_router(health_api.router)
     return app
 
 app = create_app()
diff --git a/app/models/__init__.py b/app/models/__init__.py
new file mode 100644
index 0000000..e69de29
diff --git a/app/models/api.py b/app/models/api.py
new file mode 100644
index 0000000..4ad4c46
--- /dev/null
+++ b/app/models/api.py
@@ -0,0 +1,20 @@
+from typing import Any, Optional
+from pydantic import BaseModel, Field
+
+class ChatRequest(BaseModel):
+    message: str
+    session_id: Optional[str] = None
+
+class ExecuteRequest(BaseModel):
+    intent: str
+    slots: dict[str, Any] = Field(default_factory=dict)
+    session_id: Optional[str] = None
+
+class AgentResponse(BaseModel):
+    session_id: str
+    status: str
+    intent: Optional[str] = None
+    slots: dict[str, Any] = Field(default_factory=dict)
+    missing_slots: list[str] = Field(default_factory=list)
+    result: Optional[dict[str, Any]] = None
+    reply: Optional[str] = None
diff --git a/app/models/runtime.py b/app/models/runtime.py
new file mode 100644
index 0000000..43b8087
--- /dev/null
+++ b/app/models/runtime.py
@@ -0,0 +1,12 @@
+from dataclasses import dataclass, field
+from typing import Any, Optional
+
+@dataclass
+class RuntimeResult:
+    session_id: str
+    status: str
+    intent: Optional[str] = None
+    slots: dict[str, Any] = field(default_factory=dict)
+    missing_slots: list[str] = field(default_factory=list)
+    result: Optional[dict[str, Any]] = None
+    reply: Optional[str] = None
diff --git a/tests/test_errors.py b/tests/test_errors.py
new file mode 100644
index 0000000..7fecb34
--- /dev/null
+++ b/tests/test_errors.py
@@ -0,0 +1,18 @@
+from fastapi import FastAPI
+from fastapi.testclient import TestClient
+from app.api.errors import AppError, register_exception_handlers
+
+def test_app_error_shape():
+    app = FastAPI()
+    register_exception_handlers(app)
+
+    @app.get("/boom")
+    def boom():
+        raise AppError(code="bad_request", message="missing field", details={"field": "message"})
+
+    r = TestClient(app).get("/boom")
+    assert r.status_code == 400
+    body = r.json()
+    assert body["error"]["code"] == "bad_request"
+    assert body["error"]["message"] == "missing field"
+    assert body["error"]["details"]["field"] == "message"

