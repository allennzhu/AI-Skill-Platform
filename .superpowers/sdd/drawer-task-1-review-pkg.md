# Review package: 7a502790ec0c55f4100294bae1b7af10612403c1..31c99a27c1ff244fbb825f1e634618002bfeffd5
## Commits
31c99a2 feat: add configurable CORS for frontend agent access

## Files changed
 .env.example       |  1 +
 app/config.py      |  1 +
 app/main.py        |  9 +++++++++
 tests/test_cors.py | 16 ++++++++++++++++
 4 files changed, 27 insertions(+)

## Diff
diff --git a/.env.example b/.env.example
index d35e869..854a7ac 100644
--- a/.env.example
+++ b/.env.example
@@ -1,7 +1,8 @@
 HOST=0.0.0.0
 PORT=8000
 LLM_BASE_URL=http://127.0.0.1:11434/v1
 LLM_API_KEY=ollama
 LLM_MODEL=deepseek-r1
 LLM_TIMEOUT_SECONDS=120
 SESSION_TTL_SECONDS=3600
+CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080
diff --git a/app/config.py b/app/config.py
index c4a923e..ebb3783 100644
--- a/app/config.py
+++ b/app/config.py
@@ -3,13 +3,14 @@ from pydantic_settings import BaseSettings, SettingsConfigDict
 class Settings(BaseSettings):
     model_config = SettingsConfigDict(env_file=".env", extra="ignore")
 
     host: str = "0.0.0.0"
     port: int = 8000
     llm_base_url: str = "http://127.0.0.1:11434/v1"
     llm_api_key: str = "ollama"
     llm_model: str = "deepseek-r1"
     llm_timeout_seconds: float = 120
     session_ttl_seconds: int = 3600
+    cors_origins: str = "http://localhost:8080,http://127.0.0.1:8080"
 
 def get_settings() -> Settings:
     return Settings()
diff --git a/app/main.py b/app/main.py
index 59b4baf..6865cd0 100644
--- a/app/main.py
+++ b/app/main.py
@@ -1,30 +1,39 @@
 from pathlib import Path
 
 from fastapi import FastAPI
+from fastapi.middleware.cors import CORSMiddleware
 
 from app.api.errors import register_exception_handlers
 from app.api.v1 import chat as chat_api
 from app.api.v1 import execute as execute_api
 from app.api.v1 import health as health_api
 from app.config import get_settings
 from app.conversation.controller import ConversationController
 from app.llm.client import HttpLLMClient, LLMClient
 from app.runtime.registry import SkillRegistry
 from app.runtime.service import RuntimeService
 from app.runtime.session import SessionStore
 
 
 def create_app(llm_client: LLMClient | None = None) -> FastAPI:
     settings = get_settings()
     skills_root = Path(__file__).resolve().parent / "skills"
     app = FastAPI(title="AI Skill Platform")
+    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
+    app.add_middleware(
+        CORSMiddleware,
+        allow_origins=origins,
+        allow_credentials=True,
+        allow_methods=["*"],
+        allow_headers=["*"],
+    )
     app.state.settings = settings
     app.state.runtime = RuntimeService(
         registry=SkillRegistry.load_dir(skills_root),
         sessions=SessionStore(ttl_seconds=settings.session_ttl_seconds),
     )
     app.state.llm_client = llm_client or HttpLLMClient(settings)
     app.state.conversation = ConversationController(
         app.state.runtime,
         app.state.llm_client,
     )
diff --git a/tests/test_cors.py b/tests/test_cors.py
new file mode 100644
index 0000000..a4ce157
--- /dev/null
+++ b/tests/test_cors.py
@@ -0,0 +1,16 @@
+from fastapi.testclient import TestClient
+
+from app.main import create_app
+
+
+def test_cors_allows_configured_origin(monkeypatch):
+    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:8080")
+    client = TestClient(create_app())
+    r = client.options(
+        "/health",
+        headers={
+            "Origin": "http://localhost:8080",
+            "Access-Control-Request-Method": "GET",
+        },
+    )
+    assert r.headers.get("access-control-allow-origin") == "http://localhost:8080"

