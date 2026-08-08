### Task 1: Agent CORS

**Files:**
- Modify: `E:\AI-Skill-Platform\app\config.py`
- Modify: `E:\AI-Skill-Platform\app\main.py`
- Modify: `E:\AI-Skill-Platform\.env.example`
- Create: `E:\AI-Skill-Platform\tests\test_cors.py`

**Interfaces:**
- Consumes: `create_app`, `Settings`
- Produces: `Settings.cors_origins: str`（逗号分隔）；`create_app` 注册 `CORSMiddleware`；`OPTIONS`/`GET /health` 对允许 Origin 返回 CORS 头

- [ ] **Step 1: 写失败测试**

```python
from fastapi.testclient import TestClient
from app.main import create_app

def test_cors_allows_configured_origin(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:8080")
    # Settings 可能已缓存：确保 create_app 使用新 Settings
    from app.config import get_settings
    get_settings.cache_clear() if hasattr(get_settings, "cache_clear") else None
    client = TestClient(create_app())
    r = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:8080",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert r.headers.get("access-control-allow-origin") == "http://localhost:8080"
```

若 `get_settings` 无 lru_cache，在 `create_app` 内始终 `Settings()` 新实例即可（当前已是 `get_settings()` 每次 `Settings()`——确认后测试直接 `monkeypatch.setenv` 再 `create_app()`）。

- [ ] **Step 2: 运行确认失败**

Run: `E:\AI-Skill-Platform\.venv\Scripts\pytest tests\test_cors.py -v`  
Expected: FAIL（无 CORS 头）

- [ ] **Step 3: 实现**

`config.py` 增加：
```python
cors_origins: str = "http://localhost:8080,http://127.0.0.1:8080"
```

`main.py` 在创建 app 后：
```python
from fastapi.middleware.cors import CORSMiddleware
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

`.env.example` 增加 `CORS_ORIGINS=...`

- [ ] **Step 4: 测试通过** → `pytest tests/test_cors.py -v` 与全量 `pytest -v`

- [ ] **Step 5: Commit**（在 AI-Skill-Platform）

```bash
git add app/config.py app/main.py .env.example tests/test_cors.py
git commit -m "feat: add configurable CORS for frontend agent access"
```

---

