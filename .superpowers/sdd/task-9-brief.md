### Task 9: LLM JSON 解析 + HttpLLMClient

**Files:**
- Create: `E:\AI-Skill-Platform\app\llm\parse.py`
- Create: `E:\AI-Skill-Platform\app\llm\prompt.py`
- Create: `E:\AI-Skill-Platform\app\llm\client.py`
- Create: `E:\AI-Skill-Platform\tests\test_llm_parse.py`

**Interfaces:**
- Produces:
  - `parse_intent_json(text: str) -> dict` → `{"intent": str, "slots": dict}`；失败 raise `AppError(code="llm_error", ...)`
  - `build_system_prompt(intents_doc: str) -> str`
  - `LLMClient` Protocol: `complete(system: str, user: str) -> str`
  - `HttpLLMClient(settings).complete(...)` POST `{base}/chat/completions`
  - `FakeLLMClient(scripted: str | Callable)` 供测试

- [ ] **Step 1: 测试 parse**

```python
from app.llm.parse import parse_intent_json
from app.api.errors import AppError
import pytest

def test_parse_plain_json():
    assert parse_intent_json('{"intent":"echo","slots":{"text":"x"}}')["intent"] == "echo"

def test_parse_fenced_json():
    raw = '```json\n{"intent":"echo","slots":{}}\n```'
    assert parse_intent_json(raw)["slots"] == {}

def test_parse_invalid():
    with pytest.raises(AppError) as ei:
        parse_intent_json("not json")
    assert ei.value.code == "llm_error"
```

- [ ] **Step 2–4: 实现 parse（去围栏、json.loads、校验 intent 键）；prompt 模板；HttpLLMClient 用 httpx**

`HttpLLMClient.complete` 请求体：
```python
{
  "model": settings.llm_model,
  "messages": [
    {"role": "system", "content": system},
    {"role": "user", "content": user},
  ],
  "temperature": 0,
}
```
从 `choices[0].message.content` 取文本。HTTP 失败 → `AppError(llm_error, status_code=502)`。

- [ ] **Step 5: Commit** → `feat: add LLM client and JSON parser`

---

