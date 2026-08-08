### Task 10: Conversation + `POST /v1/chat`

**Files:**
- Create: `E:\AI-Skill-Platform\app\conversation\controller.py`
- Create: `E:\AI-Skill-Platform\app\api\v1\chat.py`
- Modify: `E:\AI-Skill-Platform\app\main.py` / `deps.py`
- Create: `E:\AI-Skill-Platform\tests\test_chat_api.py`

**Interfaces:**
- Consumes: LLMClient, RuntimeService, prompt builder, parse_intent_json
- Produces: `ConversationController.handle_chat(message, session_id) -> RuntimeResult`；`POST /v1/chat`

- [ ] **Step 1: 测试（FakeLLM）**

在 `create_app` 支持注入 `llm_client`（参数或 `app.state`）：

```python
from fastapi.testclient import TestClient
from app.main import create_app
from app.llm.client import FakeLLMClient

def test_chat_echo_with_fake_llm():
    fake = FakeLLMClient('{"intent":"echo","slots":{"text":"hello"}}')
    client = TestClient(create_app(llm_client=fake))
    r = client.post("/v1/chat", json={"message": "say hello"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["result"]["echo"] == "hello"

def test_chat_need_slot():
    fake = FakeLLMClient('{"intent":"echo","slots":{}}')
    client = TestClient(create_app(llm_client=fake))
    r = client.post("/v1/chat", json={"message": "echo something"})
    assert r.json()["status"] == "need_slot"

def test_chat_llm_error():
    fake = FakeLLMClient("NOT_JSON")
    client = TestClient(create_app(llm_client=fake))
    r = client.post("/v1/chat", json={"message": "hi"})
    assert r.status_code == 200
    assert r.json()["status"] == "llm_error"
```

说明：`llm_error` 与 `unknown_intent` 同样用 **200 + status**，便于客户端统一分支；`AppError` 仅用于请求体校验等。

Controller 伪代码：
```python
def handle_chat(self, message: str, session_id: str | None) -> RuntimeResult:
    if not message or not message.strip():
        raise AppError("bad_request", "message is required")
    intents_doc = self.runtime.registry.prompt_catalog()
    system = build_system_prompt(intents_doc)
    try:
        raw = self.llm.complete(system, message)
        parsed = parse_intent_json(raw)
    except AppError as e:
        if e.code == "llm_error":
            sid = session_id or self.runtime.sessions.create().session_id
            return RuntimeResult(session_id=sid, status="llm_error", reply=e.message)
        raise
    return self.runtime.run(parsed["intent"], parsed.get("slots") or {}, session_id)
```

- [ ] **Step 2–4: 实现并测试通过**

- [ ] **Step 5: Commit** → `feat: add chat endpoint with pluggable LLM`

---

