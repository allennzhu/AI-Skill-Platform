# Review package: c2ee94ae237cdecee915abaae2a8c2211b5a0818..9aee1e46e6e685a46201c99b491222bbf0b30895

## Commits
9aee1e4 chore: add gitignore and untrack pycache
5b5d090 feat: scaffold FastAPI app with /health

## Files changed
 .gitignore                                      |   5 +++++
 app/__init__.py                                 |   0
 app/api/__init__.py                             |   0
 app/api/__pycache__/__init__.cpython-314.pyc    | Bin 0 -> 139 bytes
 app/api/v1/__init__.py                          |   0
 app/api/v1/__pycache__/__init__.cpython-314.pyc | Bin 0 -> 142 bytes
 app/api/v1/__pycache__/health.cpython-314.pyc   | Bin 0 -> 415 bytes
 app/api/v1/health.py                            |   7 +++++++
 app/config.py                                   |  14 ++++++++++++++
 app/main.py                                     |   9 +++++++++
 pytest.ini                                      |   4 ++++
 requirements.txt                                |   8 ++++++++
 tests/conftest.py                               |   1 +
 tests/test_health.py                            |   8 ++++++++
 14 files changed, 56 insertions(+)

## Diff
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
diff --git a/app/__init__.py b/app/__init__.py
new file mode 100644
index 0000000..e69de29
diff --git a/app/api/__init__.py b/app/api/__init__.py
new file mode 100644
index 0000000..e69de29
diff --git a/app/api/__pycache__/__init__.cpython-314.pyc b/app/api/__pycache__/__init__.cpython-314.pyc
new file mode 100644
index 0000000..f744a54
Binary files /dev/null and b/app/api/__pycache__/__init__.cpython-314.pyc differ
diff --git a/app/api/v1/__init__.py b/app/api/v1/__init__.py
new file mode 100644
index 0000000..e69de29
diff --git a/app/api/v1/__pycache__/__init__.cpython-314.pyc b/app/api/v1/__pycache__/__init__.cpython-314.pyc
new file mode 100644
index 0000000..715546d
Binary files /dev/null and b/app/api/v1/__pycache__/__init__.cpython-314.pyc differ
diff --git a/app/api/v1/__pycache__/health.cpython-314.pyc b/app/api/v1/__pycache__/health.cpython-314.pyc
new file mode 100644
index 0000000..8031954
Binary files /dev/null and b/app/api/v1/__pycache__/health.cpython-314.pyc differ
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
diff --git a/app/main.py b/app/main.py
new file mode 100644
index 0000000..0c9cc6b
--- /dev/null
+++ b/app/main.py
@@ -0,0 +1,9 @@
+from fastapi import FastAPI
+from app.api.v1 import health as health_api
+
+def create_app() -> FastAPI:
+    app = FastAPI(title="AI Skill Platform")
+    app.include_router(health_api.router)
+    return app
+
+app = create_app()
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

