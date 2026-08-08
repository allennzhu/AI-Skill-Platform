### Task 4: Skill 协议 + echo / health

**Files:**
- Create: `E:\AI-Skill-Platform\app\skills\base.py`
- Create: `E:\AI-Skill-Platform\app\skills\echo\manifest.yaml` + 四个 py 模块
- Create: `E:\AI-Skill-Platform\app\skills\health\manifest.yaml` + 四个 py 模块
- Create: `E:\AI-Skill-Platform\tests\test_skills_unit.py`

**Interfaces:**
- Consumes: 无
- Produces:
  - `SkillManifest`（name, intent, description, required_slots: list[str]）
  - `Skill` protocol：`validate(slots) -> None`，`normalize(slots) -> dict`，`execute(slots) -> dict`，`build_response(result) -> dict`（含 `result` 与可选 `reply`）
  - `load_skill_package(path: Path) -> tuple[SkillManifest, Skill]`

- [ ] **Step 1: 写失败测试**

```python
from pathlib import Path
from app.skills.base import load_skill_package

ROOT = Path(__file__).resolve().parents[1] / "app" / "skills"

def test_echo_skill_executes():
    manifest, skill = load_skill_package(ROOT / "echo")
    assert manifest.intent == "echo"
    assert manifest.required_slots == ["text"]
    skill.validate({"text": "hi"})
    slots = skill.normalize({"text": "hi"})
    result = skill.execute(slots)
    payload = skill.build_response(result)
    assert payload["result"] == {"echo": "hi"}

def test_health_skill_lists_skills():
    _, skill = load_skill_package(ROOT / "health")
    payload = skill.build_response(skill.execute({}))
    assert payload["result"]["runtime"] == "ok"
    assert "echo" in payload["result"]["skills"]
```

- [ ] **Step 2: 运行确认失败**

- [ ] **Step 3: 实现**

`echo/manifest.yaml`:
```yaml
name: echo
intent: echo
description: Echo back the text slot
slots:
  required:
    - name: text
      type: string
      description: Text to echo
  optional: []
```

`health/manifest.yaml`:
```yaml
name: health
intent: health
description: Runtime health skill
slots:
  required: []
  optional: []
```

`app/skills/base.py`：用 importlib 动态加载同目录 `validator/normalizer/executor/response` 模块；解析 YAML 得到 `required_slots`。

`echo/executor.py` 返回 `{"echo": slots["text"]}`；`echo/response.py` 返回 `{"result": result, "reply": f"echo: {result['echo']}"}`。

`health/executor.py` 返回 `{"runtime": "ok", "skills": ["echo", "health"]}`。

validator：echo 若缺 `text` 或非 str 则 `raise ValueError("text required")`（Runtime 缺槽应在 SlotManager 先拦；validator 做类型兜底）。

- [ ] **Step 4: 测试通过**

- [ ] **Step 5: Commit** → `feat: add echo and health placeholder skills`

---

