# Review package: 343ea9b8035980d925ae5f753f42ecffc8c60f9b..3aef7e48281089669bc644f4d93f654a5886909b
## Commits
3aef7e4 feat: add chat endpoint with pluggable LLM

## Files changed
 .superpowers/sdd/task-10-report.md | 13 +++++++++++
 app/api/deps.py                    |  5 +++++
 app/api/v1/chat.py                 | 17 ++++++++++++++
 app/conversation/controller.py     | 46 ++++++++++++++++++++++++++++++++++++++
 app/main.py                        | 11 ++++++++-
 app/runtime/registry.py            | 10 +++++++++
 tests/test_chat_api.py             | 42 ++++++++++++++++++++++++++++++++++
 tests/test_registry.py             | 10 +++++++++
 8 files changed, 153 insertions(+), 1 deletion(-)

## Diff
diff --git a/.superpowers/sdd/task-10-report.md b/.superpowers/sdd/task-10-report.md
new file mode 100644
index 0000000..35df5bd
--- /dev/null
+++ b/.superpowers/sdd/task-10-report.md
@@ -0,0 +1,13 @@
+# Task 10 Report
+
+## Implemented
+- Added `SkillRegistry.prompt_catalog()` with intent descriptions and required slots.
+- Added `ConversationController` for prompt construction, LLM parsing, runtime dispatch, blank-message validation, and HTTP-200 `llm_error` results.
+- Added injectable/default LLM setup in `create_app` and stored the client/controller on `app.state`.
+- Added `POST /v1/chat` returning `AgentResponse` for `ok`, `need_slot`, and `llm_error`.
+- Added FakeLLM API coverage plus blank-message and prompt-catalog tests.
+
+## Verification
+- `.venv\Scripts\pytest -q`
+- Result: `29 passed, 1 warning`
+- Warning: existing Starlette `httpx` deprecation warning.
diff --git a/app/api/deps.py b/app/api/deps.py
index 869fe3d..d9f28ed 100644
--- a/app/api/deps.py
+++ b/app/api/deps.py
@@ -1,7 +1,12 @@
 from fastapi import Request
 
+from app.conversation.controller import ConversationController
 from app.runtime.service import RuntimeService
 
 
 def get_runtime(request: Request) -> RuntimeService:
     return request.app.state.runtime
+
+
+def get_conversation_controller(request: Request) -> ConversationController:
+    return request.app.state.conversation
diff --git a/app/api/v1/chat.py b/app/api/v1/chat.py
new file mode 100644
index 0000000..d01a72b
--- /dev/null
+++ b/app/api/v1/chat.py
@@ -0,0 +1,17 @@
+from fastapi import APIRouter, Depends
+
+from app.api.deps import get_conversation_controller
+from app.conversation.controller import ConversationController
+from app.models.api import AgentResponse, ChatRequest
+
+
+router = APIRouter()
+
+
+@router.post("/v1/chat", response_model=AgentResponse)
+def chat(
+    body: ChatRequest,
+    controller: ConversationController = Depends(get_conversation_controller),
+):
+    result = controller.handle_chat(body.message, body.session_id)
+    return AgentResponse(**result.__dict__)
diff --git a/app/conversation/controller.py b/app/conversation/controller.py
new file mode 100644
index 0000000..7a57841
--- /dev/null
+++ b/app/conversation/controller.py
@@ -0,0 +1,46 @@
+from app.api.errors import AppError
+from app.llm.client import LLMClient
+from app.llm.parse import parse_intent_json
+from app.llm.prompt import build_system_prompt
+from app.models.runtime import RuntimeResult
+from app.runtime.service import RuntimeService
+
+
+class ConversationController:
+    def __init__(self, runtime: RuntimeService, llm: LLMClient) -> None:
+        self.runtime = runtime
+        self.llm = llm
+
+    def handle_chat(
+        self,
+        message: str,
+        session_id: str | None,
+    ) -> RuntimeResult:
+        if not message or not message.strip():
+            raise AppError("bad_request", "message is required")
+
+        system = build_system_prompt(self.runtime.registry.prompt_catalog())
+        try:
+            raw = self.llm.complete(system, message)
+            parsed = parse_intent_json(raw)
+        except AppError as exc:
+            if exc.code != "llm_error":
+                raise
+            session = (
+                self.runtime.sessions.get(session_id)
+                if session_id
+                else None
+            )
+            if session is None:
+                session = self.runtime.sessions.create(session_id)
+            return RuntimeResult(
+                session_id=session.session_id,
+                status="llm_error",
+                reply=exc.message,
+            )
+
+        return self.runtime.run(
+            parsed["intent"],
+            parsed.get("slots") or {},
+            session_id,
+        )
diff --git a/app/main.py b/app/main.py
index 0748db6..59b4baf 100644
--- a/app/main.py
+++ b/app/main.py
@@ -1,28 +1,37 @@
 from pathlib import Path
 
 from fastapi import FastAPI
 
 from app.api.errors import register_exception_handlers
+from app.api.v1 import chat as chat_api
 from app.api.v1 import execute as execute_api
 from app.api.v1 import health as health_api
 from app.config import get_settings
+from app.conversation.controller import ConversationController
+from app.llm.client import HttpLLMClient, LLMClient
 from app.runtime.registry import SkillRegistry
 from app.runtime.service import RuntimeService
 from app.runtime.session import SessionStore
 
 
-def create_app() -> FastAPI:
+def create_app(llm_client: LLMClient | None = None) -> FastAPI:
     settings = get_settings()
     skills_root = Path(__file__).resolve().parent / "skills"
     app = FastAPI(title="AI Skill Platform")
     app.state.settings = settings
     app.state.runtime = RuntimeService(
         registry=SkillRegistry.load_dir(skills_root),
         sessions=SessionStore(ttl_seconds=settings.session_ttl_seconds),
     )
+    app.state.llm_client = llm_client or HttpLLMClient(settings)
+    app.state.conversation = ConversationController(
+        app.state.runtime,
+        app.state.llm_client,
+    )
     register_exception_handlers(app)
     app.include_router(health_api.router)
     app.include_router(execute_api.router)
+    app.include_router(chat_api.router)
     return app
 
 app = create_app()
diff --git a/app/runtime/registry.py b/app/runtime/registry.py
index 41fe884..5bf4d89 100644
--- a/app/runtime/registry.py
+++ b/app/runtime/registry.py
@@ -30,10 +30,20 @@ class SkillRegistry:
             if manifest.intent == "unknown":
                 continue
             skills[manifest.intent] = RegisteredSkill(manifest=manifest, skill=skill)
         return cls(skills)
 
     def get(self, intent: str) -> RegisteredSkill | None:
         return self._skills.get(intent)
 
     def list_intents(self) -> list[str]:
         return sorted(self._skills.keys())
+
+    def prompt_catalog(self) -> str:
+        lines = []
+        for intent in self.list_intents():
+            manifest = self._skills[intent].manifest
+            required = ", ".join(manifest.required_slots) or "none"
+            lines.append(
+                f"- {intent}: {manifest.description}; required slots: {required}"
+            )
+        return "\n".join(lines)
diff --git a/tests/test_chat_api.py b/tests/test_chat_api.py
new file mode 100644
index 0000000..5328854
--- /dev/null
+++ b/tests/test_chat_api.py
@@ -0,0 +1,42 @@
+from fastapi.testclient import TestClient
+
+from app.llm.client import FakeLLMClient
+from app.main import create_app
+
+
+def test_chat_echo_with_fake_llm():
+    fake = FakeLLMClient('{"intent":"echo","slots":{"text":"hello"}}')
+    client = TestClient(create_app(llm_client=fake))
+    response = client.post("/v1/chat", json={"message": "say hello"})
+
+    assert response.status_code == 200
+    body = response.json()
+    assert body["status"] == "ok"
+    assert body["result"]["echo"] == "hello"
+
+
+def test_chat_need_slot():
+    fake = FakeLLMClient('{"intent":"echo","slots":{}}')
+    client = TestClient(create_app(llm_client=fake))
+    response = client.post("/v1/chat", json={"message": "echo something"})
+
+    assert response.status_code == 200
+    assert response.json()["status"] == "need_slot"
+
+
+def test_chat_llm_error():
+    fake = FakeLLMClient("NOT_JSON")
+    client = TestClient(create_app(llm_client=fake))
+    response = client.post("/v1/chat", json={"message": "hi"})
+
+    assert response.status_code == 200
+    assert response.json()["status"] == "llm_error"
+
+
+def test_chat_rejects_blank_message():
+    fake = FakeLLMClient('{"intent":"echo","slots":{"text":"unused"}}')
+    client = TestClient(create_app(llm_client=fake))
+    response = client.post("/v1/chat", json={"message": "   "})
+
+    assert response.status_code == 400
+    assert response.json()["error"]["code"] == "bad_request"
diff --git a/tests/test_registry.py b/tests/test_registry.py
index 8d6086b..5fe4614 100644
--- a/tests/test_registry.py
+++ b/tests/test_registry.py
@@ -7,20 +7,30 @@ from app.runtime.registry import SkillRegistry
 from app.runtime.router import Router
 
 ROOT = Path(__file__).resolve().parents[1] / "app" / "skills"
 
 
 def test_registry_loads_echo_and_health():
     reg = SkillRegistry.load_dir(ROOT)
     assert set(reg.list_intents()) >= {"echo", "health"}
 
 
+def test_registry_prompt_catalog_lists_intents_and_required_slots():
+    reg = SkillRegistry.load_dir(ROOT)
+
+    catalog = reg.prompt_catalog()
+
+    assert "echo" in catalog
+    assert "text" in catalog
+    assert "health" in catalog
+
+
 def test_router_unknown_intent():
     reg = SkillRegistry.load_dir(ROOT)
     router = Router(reg)
     with pytest.raises(AppError) as ei:
         router.resolve("nope")
     assert ei.value.code == "unknown_intent"
 
 
 def test_router_literal_unknown_intent():
     reg = SkillRegistry.load_dir(ROOT)

