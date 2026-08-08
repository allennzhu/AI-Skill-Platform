### Task 1: 工程脚手架 + `/health`

**Files:**
- Create: `E:\AI-Skill-Platform\requirements.txt`
- Create: `E:\AI-Skill-Platform\pytest.ini`
- Create: `E:\AI-Skill-Platform\app\__init__.py`
- Create: `E:\AI-Skill-Platform\app\config.py`
- Create: `E:\AI-Skill-Platform\app\main.py`
- Create: `E:\AI-Skill-Platform\app\api\__init__.py`
- Create: `E:\AI-Skill-Platform\app\api\v1\__init__.py`
- Create: `E:\AI-Skill-Platform\app\api\v1\health.py`
- Create: `E:\AI-Skill-Platform\tests\conftest.py`
- Create: `E:\AI-Skill-Platform\tests\test_health.py`

**Interfaces:**
- Consumes: 无
- Produces: `create_app() -> FastAPI`；`Settings`（`host`, `port`, `llm_base_url`, `llm_api_key`, `llm_model`, `session_ttl_seconds`）；`GET /health` → `{"status":"ok"}`

- [ ] **Step 1: 初始化目录与依赖文件**

在 `E:\AI-Skill-Platform` 创建目录结构（空 `__init__.py` 可先建）。写入：

`requirements.txt`:
```text
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
httpx>=0.27.0
pydantic>=2.9.0
pydantic-settings>=2.6.0
pytest>=8.3.0
pytest-asyncio>=0.24.0
pyyaml>=6.0.2
```

`pytest.ini`:
```ini
[pytest]
asyncio_mode = auto
pythonpath = .
testpaths = tests
```

- [ ] **Step 2: 写失败测试**

`tests/test_health.py`:
```python
from fastapi.testclient import TestClient
from app.main import create_app

def test_health_returns_ok():
    client = TestClient(create_app())
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
```

- [ ] **Step 3: 运行确认失败**

Run: `cd E:\AI-Skill-Platform && python -m venv .venv && .\.venv\Scripts\pip install -r requirements.txt && .\.venv\Scripts\pytest tests\test_health.py -v`

Expected: FAIL（`app.main` / `create_app` 不存在）

- [ ] **Step 4: 最小实现**

`app/config.py`:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    host: str = "0.0.0.0"
    port: int = 8000
    llm_base_url: str = "http://127.0.0.1:11434/v1"
    llm_api_key: str = "ollama"
    llm_model: str = "deepseek-r1"
    session_ttl_seconds: int = 3600

def get_settings() -> Settings:
    return Settings()
```

`app/api/v1/health.py`:
```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok"}
```

`app/main.py`:
```python
from fastapi import FastAPI
from app.api.v1 import health as health_api

def create_app() -> FastAPI:
    app = FastAPI(title="AI Skill Platform")
    app.include_router(health_api.router)
    return app

app = create_app()
```

`tests/conftest.py`:
```python
# reserved for shared fixtures
```

- [ ] **Step 5: 运行确认通过**

Run: `E:\AI-Skill-Platform\.venv\Scripts\pytest tests\test_health.py -v`  
Expected: PASS

- [ ] **Step 6: Commit**

```bash
cd /e/AI-Skill-Platform
git init
git add requirements.txt pytest.ini app tests
git commit -m "feat: scaffold FastAPI app with /health"
```

---

