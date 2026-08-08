### Task 8: `POST /v1/execute`

**Files:**
- Create: `E:\AI-Skill-Platform\app\api\v1\execute.py`
- Modify: `E:\AI-Skill-Platform\app\main.py`
- Create: `E:\AI-Skill-Platform\tests\test_execute_api.py`

**Interfaces:**
- Consumes: `ExecuteRequest`, `RuntimeService.run`, `AgentResponse`
- Produces: `POST /v1/execute`

- [ ] **Step 1: 测试**

```python
from fastapi.testclient import TestClient
from app.main import create_app

def test_execute_echo():
    client = TestClient(create_app())
    r = client.post("/v1/execute", json={"intent": "echo", "slots": {"text": "hi"}})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["result"]["echo"] == "hi"

def test_execute_need_slot():
    client = TestClient(create_app())
    r = client.post("/v1/execute", json={"intent": "echo", "slots": {}})
    assert r.status_code == 200
    assert r.json()["status"] == "need_slot"
    assert r.json()["missing_slots"] == ["text"]

def test_execute_health():
    client = TestClient(create_app())
    r = client.post("/v1/execute", json={"intent": "health", "slots": {}})
    assert r.status_code == 200
    assert r.json()["result"]["runtime"] == "ok"
```

- [ ] **Step 2–4: 实现路由；`create_app` lifespan 中加载 registry 并注入**

`execute` 路由伪代码：
```python
@router.post("/v1/execute", response_model=AgentResponse)
def execute(body: ExecuteRequest, runtime: RuntimeService = Depends(get_runtime)):
    if not body.intent:
        raise AppError(code="bad_request", message="intent is required")
    result = runtime.run(body.intent, body.slots, body.session_id)
    return AgentResponse(**result.__dict__)
```

确保 `TestClient(create_app())` 能拿到已加载的 Runtime（在 `create_app` 内同步构建 `app.state.runtime`，不必只靠 lifespan，便于测试）。

- [ ] **Step 5: Commit** → `feat: add POST /v1/execute`

---

