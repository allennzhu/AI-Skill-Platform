# Review package: b19b47bb4b4039f184a709fc18b1ae10406f30ea..7df0c13665d86a7d07bbdebe6e40c276d33167ae
## Commits
7df0c13 feat: add executor and runtime service

## Files changed
 .superpowers/sdd/task-7-report.md |  25 ++++++++
 app/api/deps.py                   |   7 ++
 app/main.py                       |  15 +++++
 app/runtime/executor.py           |  20 ++++++
 app/runtime/service.py            |  76 ++++++++++++++++++++++
 tests/test_executor.py            | 130 ++++++++++++++++++++++++++++++++++++++
 6 files changed, 273 insertions(+)

## Diff
diff --git a/.superpowers/sdd/task-7-report.md b/.superpowers/sdd/task-7-report.md
new file mode 100644
index 0000000..f1c3fdc
--- /dev/null
+++ b/.superpowers/sdd/task-7-report.md
@@ -0,0 +1,25 @@
+# Task 7 Report: Executor + RuntimeService
+
+## Status
+
+Implemented the skill execution pipeline, runtime orchestration, synchronous app wiring, and FastAPI runtime dependency.
+
+## Changes
+
+- Added `SkillExecutor` with `validate 鈫?normalize 鈫?execute 鈫?build_response` sequencing.
+- Converted all skill pipeline exceptions to `AppError(code="skill_error", status_code=500)`.
+- Added `RuntimeService` with session creation/reuse, slot merging, intent routing, missing-slot responses, skill execution, and session persistence.
+- Returned `RuntimeResult(status="unknown_intent")` for unknown intents instead of raising.
+- Added `get_runtime(request)` to read `request.app.state.runtime`.
+- Built `app.state.runtime` synchronously in `create_app()` using `get_settings()` and the configured session TTL.
+- Added focused tests for executor sequencing/errors, all runtime statuses, session slot merging, dependency lookup, and synchronous app initialization.
+
+## Verification
+
+- Red phase: `tests/test_executor.py` failed during collection because `app.runtime.executor` did not exist.
+- Focused tests: 8 passed.
+- Full suite: 18 passed.
+
+## Concerns
+
+- The existing FastAPI test client emits one `StarletteDeprecationWarning` recommending `httpx2`; it does not affect test results.
diff --git a/app/api/deps.py b/app/api/deps.py
new file mode 100644
index 0000000..869fe3d
--- /dev/null
+++ b/app/api/deps.py
@@ -0,0 +1,7 @@
+from fastapi import Request
+
+from app.runtime.service import RuntimeService
+
+
+def get_runtime(request: Request) -> RuntimeService:
+    return request.app.state.runtime
diff --git a/app/main.py b/app/main.py
index c380087..c60a40b 100644
--- a/app/main.py
+++ b/app/main.py
@@ -1,11 +1,26 @@
+from pathlib import Path
+
 from fastapi import FastAPI
+
 from app.api.errors import register_exception_handlers
 from app.api.v1 import health as health_api
+from app.config import get_settings
+from app.runtime.registry import SkillRegistry
+from app.runtime.service import RuntimeService
+from app.runtime.session import SessionStore
+
 
 def create_app() -> FastAPI:
+    settings = get_settings()
+    skills_root = Path(__file__).resolve().parent / "skills"
     app = FastAPI(title="AI Skill Platform")
+    app.state.settings = settings
+    app.state.runtime = RuntimeService(
+        registry=SkillRegistry.load_dir(skills_root),
+        sessions=SessionStore(ttl_seconds=settings.session_ttl_seconds),
+    )
     register_exception_handlers(app)
     app.include_router(health_api.router)
     return app
 
 app = create_app()
diff --git a/app/runtime/executor.py b/app/runtime/executor.py
new file mode 100644
index 0000000..a56f2ea
--- /dev/null
+++ b/app/runtime/executor.py
@@ -0,0 +1,20 @@
+from typing import Any
+
+from app.api.errors import AppError
+from app.skills.base import Skill
+
+
+class SkillExecutor:
+    def run(self, skill: Skill, slots: dict[str, Any]) -> dict[str, Any]:
+        try:
+            skill.validate(slots)
+            normalized = skill.normalize(slots)
+            result = skill.execute(normalized)
+            return skill.build_response(result)
+        except Exception as exc:
+            raise AppError(
+                code="skill_error",
+                message="Skill execution failed",
+                details={"reason": str(exc)},
+                status_code=500,
+            ) from exc
diff --git a/app/runtime/service.py b/app/runtime/service.py
new file mode 100644
index 0000000..f180d7e
--- /dev/null
+++ b/app/runtime/service.py
@@ -0,0 +1,76 @@
+from typing import Any
+
+from app.api.errors import AppError
+from app.models.runtime import RuntimeResult
+from app.runtime.executor import SkillExecutor
+from app.runtime.registry import SkillRegistry
+from app.runtime.router import Router
+from app.runtime.session import SessionStore
+from app.runtime.slot_manager import SlotManager
+
+
+class RuntimeService:
+    def __init__(
+        self,
+        registry: SkillRegistry,
+        sessions: SessionStore,
+        router: Router | None = None,
+        slot_manager: SlotManager | None = None,
+        executor: SkillExecutor | None = None,
+    ) -> None:
+        self.registry = registry
+        self.sessions = sessions
+        self.router = router or Router(registry)
+        self.slot_manager = slot_manager or SlotManager()
+        self.executor = executor or SkillExecutor()
+
+    def run(
+        self,
+        intent: str,
+        slots: dict[str, Any],
+        session_id: str | None,
+    ) -> RuntimeResult:
+        session = self.sessions.get(session_id) if session_id else None
+        if session is None:
+            session = self.sessions.create(session_id)
+
+        self.sessions.merge_slots(session, intent, slots)
+
+        try:
+            registered = self.router.resolve(intent)
+        except AppError as exc:
+            if exc.code != "unknown_intent":
+                raise
+            self.sessions.save(session)
+            return RuntimeResult(
+                session_id=session.session_id,
+                status="unknown_intent",
+                intent=intent,
+                slots=dict(session.slots),
+            )
+
+        missing_slots = self.slot_manager.missing(
+            registered.manifest.required_slots,
+            session.slots,
+        )
+        if missing_slots:
+            self.sessions.save(session)
+            return RuntimeResult(
+                session_id=session.session_id,
+                status="need_slot",
+                intent=intent,
+                slots=dict(session.slots),
+                missing_slots=missing_slots,
+                reply=f"璇疯ˉ鍏? {', '.join(missing_slots)}",
+            )
+
+        response = self.executor.run(registered.skill, session.slots)
+        self.sessions.save(session)
+        return RuntimeResult(
+            session_id=session.session_id,
+            status="ok",
+            intent=intent,
+            slots=dict(session.slots),
+            result=response.get("result"),
+            reply=response.get("reply"),
+        )
diff --git a/tests/test_executor.py b/tests/test_executor.py
new file mode 100644
index 0000000..40995b1
--- /dev/null
+++ b/tests/test_executor.py
@@ -0,0 +1,130 @@
+from pathlib import Path
+
+import pytest
+from fastapi import FastAPI, Request
+from fastapi.testclient import TestClient
+
+from app.api.errors import AppError
+from app.main import create_app
+from app.runtime.executor import SkillExecutor
+from app.runtime.registry import SkillRegistry
+from app.runtime.service import RuntimeService
+from app.runtime.session import SessionStore
+
+
+def make_runtime() -> RuntimeService:
+    root = Path(__file__).resolve().parents[1] / "app" / "skills"
+    return RuntimeService(
+        registry=SkillRegistry.load_dir(root),
+        sessions=SessionStore(ttl_seconds=3600),
+    )
+
+
+def test_executor_runs_skill_pipeline_in_order() -> None:
+    calls: list[str] = []
+
+    class RecordingSkill:
+        def validate(self, slots: dict) -> None:
+            calls.append("validate")
+
+        def normalize(self, slots: dict) -> dict:
+            calls.append("normalize")
+            return {"text": slots["text"].strip()}
+
+        def execute(self, slots: dict) -> dict:
+            calls.append("execute")
+            return {"echo": slots["text"]}
+
+        def build_response(self, result: dict) -> dict:
+            calls.append("build_response")
+            return result
+
+    result = SkillExecutor().run(RecordingSkill(), {"text": " hi "})
+
+    assert result == {"echo": "hi"}
+    assert calls == ["validate", "normalize", "execute", "build_response"]
+
+
+def test_executor_wraps_skill_exceptions() -> None:
+    class FailingSkill:
+        def validate(self, slots: dict) -> None:
+            raise ValueError("bad input")
+
+        def normalize(self, slots: dict) -> dict:
+            return slots
+
+        def execute(self, slots: dict) -> dict:
+            return slots
+
+        def build_response(self, result: dict) -> dict:
+            return result
+
+    with pytest.raises(AppError) as exc_info:
+        SkillExecutor().run(FailingSkill(), {})
+
+    assert exc_info.value.code == "skill_error"
+    assert exc_info.value.status_code == 500
+
+
+def test_runtime_echo_ok() -> None:
+    result = make_runtime().run(intent="echo", slots={"text": "hi"}, session_id=None)
+
+    assert result.status == "ok"
+    assert result.result == {"echo": "hi"}
+
+
+def test_runtime_echo_need_slot() -> None:
+    result = make_runtime().run(intent="echo", slots={}, session_id=None)
+
+    assert result.status == "need_slot"
+    assert result.missing_slots == ["text"]
+    assert result.reply == "璇疯ˉ鍏? text"
+
+
+def test_runtime_unknown_intent_returns_result() -> None:
+    result = make_runtime().run(intent="unknown", slots={}, session_id=None)
+
+    assert result.status == "unknown_intent"
+    assert result.intent == "unknown"
+    assert result.slots == {}
+
+
+def test_runtime_merges_slots_from_session() -> None:
+    runtime = make_runtime()
+    first = runtime.run(intent="echo", slots={}, session_id=None)
+
+    result = runtime.run(
+        intent="echo",
+        slots={"text": "later"},
+        session_id=first.session_id,
+    )
+
+    assert result.status == "ok"
+    assert result.slots == {"text": "later"}
+    assert result.result == {"echo": "later"}
+
+
+def test_create_app_builds_runtime_synchronously() -> None:
+    app = create_app()
+
+    assert isinstance(app.state.runtime, RuntimeService)
+    assert (
+        app.state.runtime.sessions.ttl_seconds
+        == app.state.settings.session_ttl_seconds
+    )
+
+
+def test_get_runtime_reads_app_state() -> None:
+    from app.api.deps import get_runtime
+
+    app = FastAPI()
+    expected = object()
+    app.state.runtime = expected
+
+    @app.get("/runtime")
+    def runtime_endpoint(request: Request) -> dict[str, bool]:
+        return {"matches": get_runtime(request) is expected}
+
+    response = TestClient(app).get("/runtime")
+
+    assert response.json() == {"matches": True}

