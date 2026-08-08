### Task 7: Executor + RuntimeService

**Files:**
- Create: `E:\AI-Skill-Platform\app\runtime\executor.py`
- Create: `E:\AI-Skill-Platform\app\runtime\service.py`
- Create: `E:\AI-Skill-Platform\tests\test_executor.py`
- Create: `E:\AI-Skill-Platform\app\api\deps.py`
- Modify: `E:\AI-Skill-Platform\app\main.py`（lifespan 构建 RuntimeService 挂到 `app.state`）

**Interfaces:**
- Consumes: SessionStore, SkillRegistry, Router, SlotManager, Skill
- Produces:
  - `SkillExecutor.run(skill, slots) -> dict`（validate→normalize→execute→build_response）；Skill 异常 → `AppError(code="skill_error", status_code=500)`
  - `RuntimeService.run(intent: str, slots: dict, session_id: str | None) -> RuntimeResult`
  - 逻辑：取/建 session → merge → router（`unknown`/`unknown_intent`）→ missing → 若缺：`status=need_slot`, `reply=请补充: a, b` → 否则 executor → `status=ok` → save session

- [ ] **Step 1: 测试**

```python
from pathlib import Path
from app.runtime.registry import SkillRegistry
from app.runtime.session import SessionStore
from app.runtime.service import RuntimeService

def make_runtime():
    root = Path(__file__).resolve().parents[1] / "app" / "skills"
    return RuntimeService(
        registry=SkillRegistry.load_dir(root),
        sessions=SessionStore(ttl_seconds=3600),
    )

def test_runtime_echo_ok():
    rt = make_runtime()
    res = rt.run(intent="echo", slots={"text": "hi"}, session_id=None)
    assert res.status == "ok"
    assert res.result == {"echo": "hi"}

def test_runtime_echo_need_slot():
    rt = make_runtime()
    res = rt.run(intent="echo", slots={}, session_id=None)
    assert res.status == "need_slot"
    assert res.missing_slots == ["text"]

def test_runtime_unknown_intent():
    rt = make_runtime()
    res = rt.run(intent="unknown", slots={}, session_id=None)
    assert res.status == "unknown_intent"
```

说明：`unknown_intent` 既可通过抛 `AppError` 也可通过 `RuntimeResult.status`。**本计划约定 RuntimeService 对未知 intent 返回 `RuntimeResult(status="unknown_intent", ...)`，不抛异常**；HTTP 层将其映射为 400 + error body **或** 200 + status 字段。为与 Chat 的 `need_slot`/`ok` 同形，**HTTP 对业务状态一律 200**，仅参数校验失败用 `AppError`。因此 `test_runtime_unknown_intent` 断言 `status == "unknown_intent"`。

- [ ] **Step 2–4: 实现并测试通过**

- [ ] **Step 5: Commit** → `feat: add executor and runtime service`

---

