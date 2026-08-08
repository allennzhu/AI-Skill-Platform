# Review package: 7df0c13665d86a7d07bbdebe6e40c276d33167ae..a12824721d19f92a835afd6cceeb48940e91bede
## Commits
a128247 feat: add POST /v1/execute

## Files changed
 app/api/v1/execute.py     | 16 ++++++++++++++++
 app/main.py               |  2 ++
 tests/test_execute_api.py | 27 +++++++++++++++++++++++++++
 3 files changed, 45 insertions(+)

## Diff
diff --git a/app/api/v1/execute.py b/app/api/v1/execute.py
new file mode 100644
index 0000000..b95c754
--- /dev/null
+++ b/app/api/v1/execute.py
@@ -0,0 +1,16 @@
+from fastapi import APIRouter, Depends
+
+from app.api.deps import get_runtime
+from app.api.errors import AppError
+from app.models.api import AgentResponse, ExecuteRequest
+from app.runtime.service import RuntimeService
+
+router = APIRouter()
+
+
+@router.post("/v1/execute", response_model=AgentResponse)
+def execute(body: ExecuteRequest, runtime: RuntimeService = Depends(get_runtime)):
+    if not body.intent:
+        raise AppError(code="bad_request", message="intent is required")
+    result = runtime.run(body.intent, body.slots, body.session_id)
+    return AgentResponse(**result.__dict__)
diff --git a/app/main.py b/app/main.py
index c60a40b..0748db6 100644
--- a/app/main.py
+++ b/app/main.py
@@ -1,26 +1,28 @@
 from pathlib import Path
 
 from fastapi import FastAPI
 
 from app.api.errors import register_exception_handlers
+from app.api.v1 import execute as execute_api
 from app.api.v1 import health as health_api
 from app.config import get_settings
 from app.runtime.registry import SkillRegistry
 from app.runtime.service import RuntimeService
 from app.runtime.session import SessionStore
 
 
 def create_app() -> FastAPI:
     settings = get_settings()
     skills_root = Path(__file__).resolve().parent / "skills"
     app = FastAPI(title="AI Skill Platform")
     app.state.settings = settings
     app.state.runtime = RuntimeService(
         registry=SkillRegistry.load_dir(skills_root),
         sessions=SessionStore(ttl_seconds=settings.session_ttl_seconds),
     )
     register_exception_handlers(app)
     app.include_router(health_api.router)
+    app.include_router(execute_api.router)
     return app
 
 app = create_app()
diff --git a/tests/test_execute_api.py b/tests/test_execute_api.py
new file mode 100644
index 0000000..54b7e82
--- /dev/null
+++ b/tests/test_execute_api.py
@@ -0,0 +1,27 @@
+from fastapi.testclient import TestClient
+
+from app.main import create_app
+
+
+def test_execute_echo():
+    client = TestClient(create_app())
+    r = client.post("/v1/execute", json={"intent": "echo", "slots": {"text": "hi"}})
+    assert r.status_code == 200
+    body = r.json()
+    assert body["status"] == "ok"
+    assert body["result"]["echo"] == "hi"
+
+
+def test_execute_need_slot():
+    client = TestClient(create_app())
+    r = client.post("/v1/execute", json={"intent": "echo", "slots": {}})
+    assert r.status_code == 200
+    assert r.json()["status"] == "need_slot"
+    assert r.json()["missing_slots"] == ["text"]
+
+
+def test_execute_health():
+    client = TestClient(create_app())
+    r = client.post("/v1/execute", json={"intent": "health", "slots": {}})
+    assert r.status_code == 200
+    assert r.json()["result"]["runtime"] == "ok"

