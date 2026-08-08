# Review package: c2ee94ae237cdecee915abaae2a8c2211b5a0818..db30df15fa483d003a9731a3946e465260284f36
## Commits
db30df1 docs: add README and env example
3aef7e4 feat: add chat endpoint with pluggable LLM
343ea9b feat: add LLM client and JSON parser
a128247 feat: add POST /v1/execute
7df0c13 feat: add executor and runtime service
b19b47b feat: add slot manager
b1229da feat: add skill registry and router
e873edf feat: add echo and health placeholder skills
fe39d28 feat: add in-memory session store
622bc1b feat: add API models and AppError handler
7226dd2 chore: remove remaining tracked __pycache__ from index
9aee1e4 chore: add gitignore and untrack pycache
5b5d090 feat: scaffold FastAPI app with /health

## Files changed
 .env.example                       |   6 ++
 .gitignore                         |   5 ++
 .superpowers/sdd/task-10-report.md |  13 ++++
 .superpowers/sdd/task-7-report.md  |  25 +++++++
 README.md                          |  75 +++++++++++++++++++++
 app/__init__.py                    |   0
 app/api/__init__.py                |   0
 app/api/deps.py                    |  12 ++++
 app/api/errors.py                  |  19 ++++++
 app/api/v1/__init__.py             |   0
 app/api/v1/chat.py                 |  17 +++++
 app/api/v1/execute.py              |  16 +++++
 app/api/v1/health.py               |   7 ++
 app/config.py                      |  14 ++++
 app/conversation/controller.py     |  46 +++++++++++++
 app/llm/client.py                  |  52 +++++++++++++++
 app/llm/parse.py                   |  39 +++++++++++
 app/llm/prompt.py                  |   9 +++
 app/main.py                        |  37 +++++++++++
 app/models/__init__.py             |   0
 app/models/api.py                  |  20 ++++++
 app/models/runtime.py              |  12 ++++
 app/runtime/__init__.py            |   0
 app/runtime/executor.py            |  20 ++++++
 app/runtime/registry.py            |  49 ++++++++++++++
 app/runtime/router.py              |  17 +++++
 app/runtime/service.py             |  76 ++++++++++++++++++++++
 app/runtime/session.py             |  47 ++++++++++++++
 app/runtime/slot_manager.py        |   7 ++
 app/skills/__init__.py             |   0
 app/skills/base.py                 |  91 ++++++++++++++++++++++++++
 app/skills/echo/executor.py        |   5 ++
 app/skills/echo/manifest.yaml      |   9 +++
 app/skills/echo/normalizer.py      |   5 ++
 app/skills/echo/response.py        |   5 ++
 app/skills/echo/validator.py       |   7 ++
 app/skills/health/executor.py      |   5 ++
 app/skills/health/manifest.yaml    |   6 ++
 app/skills/health/normalizer.py    |   5 ++
 app/skills/health/response.py      |   5 ++
 app/skills/health/validator.py     |   5 ++
 pytest.ini                         |   4 ++
 requirements.txt                   |   8 +++
 tests/conftest.py                  |   1 +
 tests/test_chat_api.py             |  42 ++++++++++++
 tests/test_errors.py               |  18 +++++
 tests/test_execute_api.py          |  27 ++++++++
 tests/test_executor.py             | 130 +++++++++++++++++++++++++++++++++++++
 tests/test_health.py               |   8 +++
 tests/test_llm_parse.py            |  20 ++++++
 tests/test_registry.py             |  40 ++++++++++++
 tests/test_session.py              |  25 +++++++
 tests/test_skills_unit.py          |  23 +++++++
 tests/test_slot_manager.py         |   8 +++
 54 files changed, 1142 insertions(+)

## Diff
diff --git a/.env.example b/.env.example
new file mode 100644
index 0000000..bbc0b80
--- /dev/null
+++ b/.env.example
@@ -0,0 +1,6 @@
+HOST=0.0.0.0
+PORT=8000
+LLM_BASE_URL=http://127.0.0.1:11434/v1
+LLM_API_KEY=ollama
+LLM_MODEL=deepseek-r1
+SESSION_TTL_SECONDS=3600
diff --git a/.gitignore b/.gitignore
new file mode 100644
index 0000000..ffb49fe
--- /dev/null
+++ b/.gitignore
@@ -0,0 +1,5 @@
+.venv/
+__pycache__/
+*.py[cod]
+.pytest_cache/
+.env
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
diff --git a/README.md b/README.md
new file mode 100644
index 0000000..59420a4
--- /dev/null
+++ b/README.md
@@ -0,0 +1,75 @@
+# AI Skill Platform
+
+FastAPI agent shell with LLM-driven chat and direct skill execution.
+
+## Requirements
+
+- Python 3.11+
+- Optional: local Ollama (or compatible OpenAI API) for `/v1/chat`
+
+## Install
+
+```bash
+python -m venv .venv
+# Windows
+.venv\Scripts\activate
+# Linux / macOS
+source .venv/bin/activate
+
+pip install -r requirements.txt
+cp .env.example .env   # edit LLM settings if needed
+```
+
+## Start
+
+```bash
+uvicorn app.main:app --host 0.0.0.0 --port 8000
+```
+
+Or use values from `.env` (defaults shown in `.env.example`).
+
+## API examples
+
+### Health
+
+```bash
+curl -s http://127.0.0.1:8000/health
+```
+
+Expected: `{"status":"ok"}`
+
+### Execute 鈥?echo
+
+```bash
+curl -s -X POST http://127.0.0.1:8000/v1/execute \
+  -H "Content-Type: application/json" \
+  -d "{\"intent\":\"echo\",\"slots\":{\"text\":\"hi\"}}"
+```
+
+### Execute 鈥?health skill
+
+```bash
+curl -s -X POST http://127.0.0.1:8000/v1/execute \
+  -H "Content-Type: application/json" \
+  -d "{\"intent\":\"health\",\"slots\":{}}"
+```
+
+### Chat (requires local LLM)
+
+Ensure Ollama (or configured endpoint) is running with `deepseek-r1` or your `LLM_MODEL`.
+
+```bash
+curl -s -X POST http://127.0.0.1:8000/v1/chat \
+  -H "Content-Type: application/json" \
+  -d "{\"message\":\"鎶?text 璁句负 hello 骞?echo\"}"
+```
+
+## Tests
+
+```bash
+pytest -v
+```
+
+## Optional manual smoke (local LLM)
+
+After starting the server, run the health and execute curls above, then the chat curl. Skip chat if the LLM endpoint is unavailable.
diff --git a/app/__init__.py b/app/__init__.py
new file mode 100644
index 0000000..e69de29
diff --git a/app/api/__init__.py b/app/api/__init__.py
new file mode 100644
index 0000000..e69de29
diff --git a/app/api/deps.py b/app/api/deps.py
new file mode 100644
index 0000000..d9f28ed
--- /dev/null
+++ b/app/api/deps.py
@@ -0,0 +1,12 @@
+from fastapi import Request
+
+from app.conversation.controller import ConversationController
+from app.runtime.service import RuntimeService
+
+
+def get_runtime(request: Request) -> RuntimeService:
+    return request.app.state.runtime
+
+
+def get_conversation_controller(request: Request) -> ConversationController:
+    return request.app.state.conversation
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
diff --git a/app/api/v1/__init__.py b/app/api/v1/__init__.py
new file mode 100644
index 0000000..e69de29
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
diff --git a/app/api/v1/health.py b/app/api/v1/health.py
new file mode 100644
index 0000000..fd2f109
--- /dev/null
+++ b/app/api/v1/health.py
@@ -0,0 +1,7 @@
+from fastapi import APIRouter
+
+router = APIRouter()
+
+@router.get("/health")
+def health():
+    return {"status": "ok"}
diff --git a/app/config.py b/app/config.py
new file mode 100644
index 0000000..87ce586
--- /dev/null
+++ b/app/config.py
@@ -0,0 +1,14 @@
+from pydantic_settings import BaseSettings, SettingsConfigDict
+
+class Settings(BaseSettings):
+    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
+
+    host: str = "0.0.0.0"
+    port: int = 8000
+    llm_base_url: str = "http://127.0.0.1:11434/v1"
+    llm_api_key: str = "ollama"
+    llm_model: str = "deepseek-r1"
+    session_ttl_seconds: int = 3600
+
+def get_settings() -> Settings:
+    return Settings()
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
diff --git a/app/llm/client.py b/app/llm/client.py
new file mode 100644
index 0000000..8530c54
--- /dev/null
+++ b/app/llm/client.py
@@ -0,0 +1,52 @@
+from collections.abc import Callable
+from typing import Protocol
+
+import httpx
+
+from app.api.errors import AppError
+from app.config import Settings
+
+
+class LLMClient(Protocol):
+    def complete(self, system: str, user: str) -> str: ...
+
+
+class HttpLLMClient:
+    def __init__(self, settings: Settings):
+        self.settings = settings
+
+    def complete(self, system: str, user: str) -> str:
+        try:
+            response = httpx.post(
+                f"{self.settings.llm_base_url.rstrip('/')}/chat/completions",
+                headers={"Authorization": f"Bearer {self.settings.llm_api_key}"},
+                json={
+                    "model": self.settings.llm_model,
+                    "messages": [
+                        {"role": "system", "content": system},
+                        {"role": "user", "content": user},
+                    ],
+                    "temperature": 0,
+                },
+            )
+            response.raise_for_status()
+            content = response.json()["choices"][0]["message"]["content"]
+            if not isinstance(content, str):
+                raise TypeError("LLM content must be a string")
+            return content
+        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
+            raise AppError(
+                code="llm_error",
+                message="LLM request failed",
+                status_code=502,
+            ) from exc
+
+
+class FakeLLMClient:
+    def __init__(self, scripted: str | Callable[[str, str], str]):
+        self.scripted = scripted
+
+    def complete(self, system: str, user: str) -> str:
+        if callable(self.scripted):
+            return self.scripted(system, user)
+        return self.scripted
diff --git a/app/llm/parse.py b/app/llm/parse.py
new file mode 100644
index 0000000..a58e51c
--- /dev/null
+++ b/app/llm/parse.py
@@ -0,0 +1,39 @@
+import json
+import re
+from typing import Any
+
+from app.api.errors import AppError
+
+
+_JSON_FENCE = re.compile(r"^\s*```(?:json)?\s*\n?(.*?)\n?\s*```\s*$", re.DOTALL | re.IGNORECASE)
+
+
+def parse_intent_json(text: str) -> dict[str, Any]:
+    match = _JSON_FENCE.match(text)
+    payload = match.group(1).strip() if match else text.strip()
+
+    try:
+        parsed = json.loads(payload)
+    except (json.JSONDecodeError, TypeError) as exc:
+        raise AppError(
+            code="llm_error",
+            message="LLM returned invalid JSON",
+            status_code=502,
+        ) from exc
+
+    if not isinstance(parsed, dict) or "intent" not in parsed:
+        raise AppError(
+            code="llm_error",
+            message="LLM response is missing intent",
+            status_code=502,
+        )
+
+    slots = parsed.get("slots", {})
+    if not isinstance(parsed["intent"], str) or not isinstance(slots, dict):
+        raise AppError(
+            code="llm_error",
+            message="LLM response has invalid intent or slots",
+            status_code=502,
+        )
+
+    return {"intent": parsed["intent"], "slots": slots}
diff --git a/app/llm/prompt.py b/app/llm/prompt.py
new file mode 100644
index 0000000..16298fc
--- /dev/null
+++ b/app/llm/prompt.py
@@ -0,0 +1,9 @@
+def build_system_prompt(intents_doc: str) -> str:
+    return (
+        "You route user messages to supported intents.\n"
+        "Return only a JSON object with this exact shape: "
+        '{"intent":"<intent name>","slots":{}}.\n'
+        "Do not include Markdown fences or explanatory text.\n\n"
+        "Supported intents:\n"
+        f"{intents_doc.strip()}"
+    )
diff --git a/app/main.py b/app/main.py
new file mode 100644
index 0000000..59b4baf
--- /dev/null
+++ b/app/main.py
@@ -0,0 +1,37 @@
+from pathlib import Path
+
+from fastapi import FastAPI
+
+from app.api.errors import register_exception_handlers
+from app.api.v1 import chat as chat_api
+from app.api.v1 import execute as execute_api
+from app.api.v1 import health as health_api
+from app.config import get_settings
+from app.conversation.controller import ConversationController
+from app.llm.client import HttpLLMClient, LLMClient
+from app.runtime.registry import SkillRegistry
+from app.runtime.service import RuntimeService
+from app.runtime.session import SessionStore
+
+
+def create_app(llm_client: LLMClient | None = None) -> FastAPI:
+    settings = get_settings()
+    skills_root = Path(__file__).resolve().parent / "skills"
+    app = FastAPI(title="AI Skill Platform")
+    app.state.settings = settings
+    app.state.runtime = RuntimeService(
+        registry=SkillRegistry.load_dir(skills_root),
+        sessions=SessionStore(ttl_seconds=settings.session_ttl_seconds),
+    )
+    app.state.llm_client = llm_client or HttpLLMClient(settings)
+    app.state.conversation = ConversationController(
+        app.state.runtime,
+        app.state.llm_client,
+    )
+    register_exception_handlers(app)
+    app.include_router(health_api.router)
+    app.include_router(execute_api.router)
+    app.include_router(chat_api.router)
+    return app
+
+app = create_app()
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
diff --git a/app/runtime/__init__.py b/app/runtime/__init__.py
new file mode 100644
index 0000000..e69de29
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
diff --git a/app/runtime/registry.py b/app/runtime/registry.py
new file mode 100644
index 0000000..5bf4d89
--- /dev/null
+++ b/app/runtime/registry.py
@@ -0,0 +1,49 @@
+from __future__ import annotations
+
+from dataclasses import dataclass
+from pathlib import Path
+
+from app.skills.base import Skill, SkillManifest, load_skill_package
+
+
+@dataclass
+class RegisteredSkill:
+    manifest: SkillManifest
+    skill: Skill
+
+
+class SkillRegistry:
+    def __init__(self, skills: dict[str, RegisteredSkill] | None = None) -> None:
+        self._skills = skills or {}
+
+    @classmethod
+    def load_dir(cls, skills_root: Path) -> SkillRegistry:
+        skills: dict[str, RegisteredSkill] = {}
+        root = skills_root.resolve()
+        for child in sorted(root.iterdir()):
+            if not child.is_dir():
+                continue
+            manifest_path = child / "manifest.yaml"
+            if not manifest_path.is_file():
+                continue
+            manifest, skill = load_skill_package(child)
+            if manifest.intent == "unknown":
+                continue
+            skills[manifest.intent] = RegisteredSkill(manifest=manifest, skill=skill)
+        return cls(skills)
+
+    def get(self, intent: str) -> RegisteredSkill | None:
+        return self._skills.get(intent)
+
+    def list_intents(self) -> list[str]:
+        return sorted(self._skills.keys())
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
diff --git a/app/runtime/router.py b/app/runtime/router.py
new file mode 100644
index 0000000..2375741
--- /dev/null
+++ b/app/runtime/router.py
@@ -0,0 +1,17 @@
+from __future__ import annotations
+
+from app.api.errors import AppError
+from app.runtime.registry import RegisteredSkill, SkillRegistry
+
+
+class Router:
+    def __init__(self, registry: SkillRegistry) -> None:
+        self._registry = registry
+
+    def resolve(self, intent: str) -> RegisteredSkill:
+        if intent == "unknown":
+            raise AppError(code="unknown_intent", message=f"Unknown intent: {intent}")
+        registered = self._registry.get(intent)
+        if registered is None:
+            raise AppError(code="unknown_intent", message=f"Unknown intent: {intent}")
+        return registered
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
diff --git a/app/runtime/session.py b/app/runtime/session.py
new file mode 100644
index 0000000..c6aa925
--- /dev/null
+++ b/app/runtime/session.py
@@ -0,0 +1,47 @@
+from __future__ import annotations
+
+import time
+import uuid
+from dataclasses import dataclass, field
+from typing import Any, Optional
+
+
+@dataclass
+class SessionData:
+    session_id: str
+    intent: Optional[str] = None
+    slots: dict[str, Any] = field(default_factory=dict)
+    updated_at: float = field(default_factory=time.time)
+
+
+class SessionStore:
+    def __init__(self, ttl_seconds: int = 3600):
+        self.ttl_seconds = ttl_seconds
+        self._data: dict[str, SessionData] = {}
+
+    def create(self, session_id: Optional[str] = None) -> SessionData:
+        sid = session_id or str(uuid.uuid4())
+        data = SessionData(session_id=sid)
+        self._data[sid] = data
+        return data
+
+    def get(self, session_id: str) -> Optional[SessionData]:
+        data = self._data.get(session_id)
+        if data is None:
+            return None
+        if time.time() - data.updated_at > self.ttl_seconds:
+            self._data.pop(session_id, None)
+            return None
+        return data
+
+    def save(self, data: SessionData) -> None:
+        self._data[data.session_id] = data
+
+    def merge_slots(
+        self, data: SessionData, intent: Optional[str], slots: dict[str, Any]
+    ) -> SessionData:
+        if intent:
+            data.intent = intent
+        data.slots.update(slots or {})
+        data.updated_at = time.time()
+        return data
diff --git a/app/runtime/slot_manager.py b/app/runtime/slot_manager.py
new file mode 100644
index 0000000..23d3b9d
--- /dev/null
+++ b/app/runtime/slot_manager.py
@@ -0,0 +1,7 @@
+class SlotManager:
+    def missing(self, required: list[str], slots: dict) -> list[str]:
+        out = []
+        for name in required:
+            if name not in slots or slots[name] is None or slots[name] == "":
+                out.append(name)
+        return out
diff --git a/app/skills/__init__.py b/app/skills/__init__.py
new file mode 100644
index 0000000..e69de29
diff --git a/app/skills/base.py b/app/skills/base.py
new file mode 100644
index 0000000..e8e08e2
--- /dev/null
+++ b/app/skills/base.py
@@ -0,0 +1,91 @@
+from __future__ import annotations
+
+import importlib.util
+from dataclasses import dataclass
+from pathlib import Path
+from typing import Any, Protocol, runtime_checkable
+
+import yaml
+
+
+@dataclass
+class SkillManifest:
+    name: str
+    intent: str
+    description: str
+    required_slots: list[str]
+
+
+@runtime_checkable
+class Skill(Protocol):
+    def validate(self, slots: dict[str, Any]) -> None: ...
+
+    def normalize(self, slots: dict[str, Any]) -> dict[str, Any]: ...
+
+    def execute(self, slots: dict[str, Any]) -> dict[str, Any]: ...
+
+    def build_response(self, result: dict[str, Any]) -> dict[str, Any]: ...
+
+
+class _LoadedSkill:
+    def __init__(
+        self,
+        validator: Any,
+        normalizer: Any,
+        executor: Any,
+        response: Any,
+    ) -> None:
+        self._validator = validator
+        self._normalizer = normalizer
+        self._executor = executor
+        self._response = response
+
+    def validate(self, slots: dict[str, Any]) -> None:
+        self._validator.validate(slots)
+
+    def normalize(self, slots: dict[str, Any]) -> dict[str, Any]:
+        return self._normalizer.normalize(slots)
+
+    def execute(self, slots: dict[str, Any]) -> dict[str, Any]:
+        return self._executor.execute(slots)
+
+    def build_response(self, result: dict[str, Any]) -> dict[str, Any]:
+        return self._response.build_response(result)
+
+
+def _load_module(skill_dir: Path, module_name: str) -> Any:
+    path = skill_dir / f"{module_name}.py"
+    spec = importlib.util.spec_from_file_location(
+        f"skill.{skill_dir.name}.{module_name}",
+        path,
+    )
+    if spec is None or spec.loader is None:
+        raise ImportError(f"Cannot load skill module: {path}")
+    module = importlib.util.module_from_spec(spec)
+    spec.loader.exec_module(module)
+    return module
+
+
+def _parse_manifest(skill_dir: Path) -> SkillManifest:
+    manifest_path = skill_dir / "manifest.yaml"
+    with manifest_path.open(encoding="utf-8") as f:
+        data = yaml.safe_load(f)
+    required = data.get("slots", {}).get("required", [])
+    required_slots = [slot["name"] for slot in required]
+    return SkillManifest(
+        name=data["name"],
+        intent=data["intent"],
+        description=data["description"],
+        required_slots=required_slots,
+    )
+
+
+def load_skill_package(path: Path) -> tuple[SkillManifest, Skill]:
+    skill_dir = path.resolve()
+    manifest = _parse_manifest(skill_dir)
+    validator = _load_module(skill_dir, "validator")
+    normalizer = _load_module(skill_dir, "normalizer")
+    executor = _load_module(skill_dir, "executor")
+    response = _load_module(skill_dir, "response")
+    skill = _LoadedSkill(validator, normalizer, executor, response)
+    return manifest, skill
diff --git a/app/skills/echo/executor.py b/app/skills/echo/executor.py
new file mode 100644
index 0000000..b7348fa
--- /dev/null
+++ b/app/skills/echo/executor.py
@@ -0,0 +1,5 @@
+from typing import Any
+
+
+def execute(slots: dict[str, Any]) -> dict[str, Any]:
+    return {"echo": slots["text"]}
diff --git a/app/skills/echo/manifest.yaml b/app/skills/echo/manifest.yaml
new file mode 100644
index 0000000..d87fdb0
--- /dev/null
+++ b/app/skills/echo/manifest.yaml
@@ -0,0 +1,9 @@
+name: echo
+intent: echo
+description: Echo back the text slot
+slots:
+  required:
+    - name: text
+      type: string
+      description: Text to echo
+  optional: []
diff --git a/app/skills/echo/normalizer.py b/app/skills/echo/normalizer.py
new file mode 100644
index 0000000..0f5db73
--- /dev/null
+++ b/app/skills/echo/normalizer.py
@@ -0,0 +1,5 @@
+from typing import Any
+
+
+def normalize(slots: dict[str, Any]) -> dict[str, Any]:
+    return {"text": slots["text"]}
diff --git a/app/skills/echo/response.py b/app/skills/echo/response.py
new file mode 100644
index 0000000..12ced0e
--- /dev/null
+++ b/app/skills/echo/response.py
@@ -0,0 +1,5 @@
+from typing import Any
+
+
+def build_response(result: dict[str, Any]) -> dict[str, Any]:
+    return {"result": result, "reply": f"echo: {result['echo']}"}
diff --git a/app/skills/echo/validator.py b/app/skills/echo/validator.py
new file mode 100644
index 0000000..0d99e25
--- /dev/null
+++ b/app/skills/echo/validator.py
@@ -0,0 +1,7 @@
+from typing import Any
+
+
+def validate(slots: dict[str, Any]) -> None:
+    text = slots.get("text")
+    if text is None or not isinstance(text, str):
+        raise ValueError("text required")
diff --git a/app/skills/health/executor.py b/app/skills/health/executor.py
new file mode 100644
index 0000000..f648c9f
--- /dev/null
+++ b/app/skills/health/executor.py
@@ -0,0 +1,5 @@
+from typing import Any
+
+
+def execute(slots: dict[str, Any]) -> dict[str, Any]:
+    return {"runtime": "ok", "skills": ["echo", "health"]}
diff --git a/app/skills/health/manifest.yaml b/app/skills/health/manifest.yaml
new file mode 100644
index 0000000..4c58a56
--- /dev/null
+++ b/app/skills/health/manifest.yaml
@@ -0,0 +1,6 @@
+name: health
+intent: health
+description: Runtime health skill
+slots:
+  required: []
+  optional: []
diff --git a/app/skills/health/normalizer.py b/app/skills/health/normalizer.py
new file mode 100644
index 0000000..bff89b5
--- /dev/null
+++ b/app/skills/health/normalizer.py
@@ -0,0 +1,5 @@
+from typing import Any
+
+
+def normalize(slots: dict[str, Any]) -> dict[str, Any]:
+    return dict(slots)
diff --git a/app/skills/health/response.py b/app/skills/health/response.py
new file mode 100644
index 0000000..75d7175
--- /dev/null
+++ b/app/skills/health/response.py
@@ -0,0 +1,5 @@
+from typing import Any
+
+
+def build_response(result: dict[str, Any]) -> dict[str, Any]:
+    return {"result": result}
diff --git a/app/skills/health/validator.py b/app/skills/health/validator.py
new file mode 100644
index 0000000..34685aa
--- /dev/null
+++ b/app/skills/health/validator.py
@@ -0,0 +1,5 @@
+from typing import Any
+
+
+def validate(slots: dict[str, Any]) -> None:
+    return None
diff --git a/pytest.ini b/pytest.ini
new file mode 100644
index 0000000..5d7a6a4
--- /dev/null
+++ b/pytest.ini
@@ -0,0 +1,4 @@
+[pytest]
+asyncio_mode = auto
+pythonpath = .
+testpaths = tests
diff --git a/requirements.txt b/requirements.txt
new file mode 100644
index 0000000..dae357d
--- /dev/null
+++ b/requirements.txt
@@ -0,0 +1,8 @@
+fastapi>=0.115.0
+uvicorn[standard]>=0.32.0
+httpx>=0.27.0
+pydantic>=2.9.0
+pydantic-settings>=2.6.0
+pytest>=8.3.0
+pytest-asyncio>=0.24.0
+pyyaml>=6.0.2
diff --git a/tests/conftest.py b/tests/conftest.py
new file mode 100644
index 0000000..73df8db
--- /dev/null
+++ b/tests/conftest.py
@@ -0,0 +1 @@
+# reserved for shared fixtures
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
diff --git a/tests/test_health.py b/tests/test_health.py
new file mode 100644
index 0000000..f53bd79
--- /dev/null
+++ b/tests/test_health.py
@@ -0,0 +1,8 @@
+from fastapi.testclient import TestClient
+from app.main import create_app
+
+def test_health_returns_ok():
+    client = TestClient(create_app())
+    r = client.get("/health")
+    assert r.status_code == 200
+    assert r.json()["status"] == "ok"
diff --git a/tests/test_llm_parse.py b/tests/test_llm_parse.py
new file mode 100644
index 0000000..62fe03e
--- /dev/null
+++ b/tests/test_llm_parse.py
@@ -0,0 +1,20 @@
+import pytest
+
+from app.api.errors import AppError
+from app.llm.parse import parse_intent_json
+
+
+def test_parse_plain_json():
+    assert parse_intent_json('{"intent":"echo","slots":{"text":"x"}}')["intent"] == "echo"
+
+
+def test_parse_fenced_json():
+    raw = '```json\n{"intent":"echo","slots":{}}\n```'
+    assert parse_intent_json(raw)["slots"] == {}
+
+
+def test_parse_invalid():
+    with pytest.raises(AppError) as exc_info:
+        parse_intent_json("not json")
+
+    assert exc_info.value.code == "llm_error"
diff --git a/tests/test_registry.py b/tests/test_registry.py
new file mode 100644
index 0000000..5fe4614
--- /dev/null
+++ b/tests/test_registry.py
@@ -0,0 +1,40 @@
+from pathlib import Path
+
+import pytest
+
+from app.api.errors import AppError
+from app.runtime.registry import SkillRegistry
+from app.runtime.router import Router
+
+ROOT = Path(__file__).resolve().parents[1] / "app" / "skills"
+
+
+def test_registry_loads_echo_and_health():
+    reg = SkillRegistry.load_dir(ROOT)
+    assert set(reg.list_intents()) >= {"echo", "health"}
+
+
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
+def test_router_unknown_intent():
+    reg = SkillRegistry.load_dir(ROOT)
+    router = Router(reg)
+    with pytest.raises(AppError) as ei:
+        router.resolve("nope")
+    assert ei.value.code == "unknown_intent"
+
+
+def test_router_literal_unknown_intent():
+    reg = SkillRegistry.load_dir(ROOT)
+    router = Router(reg)
+    with pytest.raises(AppError) as ei:
+        router.resolve("unknown")
+    assert ei.value.code == "unknown_intent"
diff --git a/tests/test_session.py b/tests/test_session.py
new file mode 100644
index 0000000..9322708
--- /dev/null
+++ b/tests/test_session.py
@@ -0,0 +1,25 @@
+import time
+from app.runtime.session import SessionStore
+
+
+def test_create_and_merge_slots():
+    store = SessionStore(ttl_seconds=60)
+    s = store.create()
+    assert s.session_id
+    s = store.merge_slots(s, intent="echo", slots={"text": "a"})
+    s = store.merge_slots(s, intent="echo", slots={"text": "b", "extra": 1})
+    assert s.slots == {"text": "b", "extra": 1}
+    assert s.intent == "echo"
+    store.save(s)
+    loaded = store.get(s.session_id)
+    assert loaded is not None
+    assert loaded.slots["text"] == "b"
+
+
+def test_expired_session_returns_none():
+    store = SessionStore(ttl_seconds=1)
+    s = store.create()
+    store.save(s)
+    s.updated_at = time.time() - 10
+    store.save(s)
+    assert store.get(s.session_id) is None
diff --git a/tests/test_skills_unit.py b/tests/test_skills_unit.py
new file mode 100644
index 0000000..b300133
--- /dev/null
+++ b/tests/test_skills_unit.py
@@ -0,0 +1,23 @@
+from pathlib import Path
+
+from app.skills.base import load_skill_package
+
+ROOT = Path(__file__).resolve().parents[1] / "app" / "skills"
+
+
+def test_echo_skill_executes():
+    manifest, skill = load_skill_package(ROOT / "echo")
+    assert manifest.intent == "echo"
+    assert manifest.required_slots == ["text"]
+    skill.validate({"text": "hi"})
+    slots = skill.normalize({"text": "hi"})
+    result = skill.execute(slots)
+    payload = skill.build_response(result)
+    assert payload["result"] == {"echo": "hi"}
+
+
+def test_health_skill_lists_skills():
+    _, skill = load_skill_package(ROOT / "health")
+    payload = skill.build_response(skill.execute({}))
+    assert payload["result"]["runtime"] == "ok"
+    assert "echo" in payload["result"]["skills"]
diff --git a/tests/test_slot_manager.py b/tests/test_slot_manager.py
new file mode 100644
index 0000000..326142d
--- /dev/null
+++ b/tests/test_slot_manager.py
@@ -0,0 +1,8 @@
+from app.runtime.slot_manager import SlotManager
+
+
+def test_missing_slots_ordered():
+    m = SlotManager()
+    assert m.missing(["text", "date"], {}) == ["text", "date"]
+    assert m.missing(["text", "date"], {"text": "x"}) == ["date"]
+    assert m.missing(["text"], {"text": "x"}) == []

