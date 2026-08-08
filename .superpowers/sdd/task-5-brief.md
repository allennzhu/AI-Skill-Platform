### Task 5: Registry + Router

**Files:**
- Create: `E:\AI-Skill-Platform\app\runtime\registry.py`
- Create: `E:\AI-Skill-Platform\app\runtime\router.py`
- Create: `E:\AI-Skill-Platform\tests\test_registry.py`

**Interfaces:**
- Consumes: `load_skill_package`
- Produces:
  - `SkillRegistry.load_dir(skills_root: Path) -> SkillRegistry`
  - `registry.get(intent: str) -> RegisteredSkill | None`
  - `registry.list_intents() -> list[str]`
  - `RegisteredSkill(manifest, skill)`
  - `Router(registry).resolve(intent: str) -> RegisteredSkill`（失败 raise `AppError(code="unknown_intent", ...)`）

- [ ] **Step 1: 测试**

```python
from pathlib import Path
from app.runtime.registry import SkillRegistry
from app.runtime.router import Router
from app.api.errors import AppError
import pytest

ROOT = Path(__file__).resolve().parents[1] / "app" / "skills"

def test_registry_loads_echo_and_health():
    reg = SkillRegistry.load_dir(ROOT)
    assert set(reg.list_intents()) >= {"echo", "health"}

def test_router_unknown_intent():
    reg = SkillRegistry.load_dir(ROOT)
    router = Router(reg)
    with pytest.raises(AppError) as ei:
        router.resolve("nope")
    assert ei.value.code == "unknown_intent"
```

- [ ] **Step 2–4: 实现并测试通过**

`SkillRegistry` 扫描子目录中含 `manifest.yaml` 的包并注册；`intent == "unknown"` 不注册为 Skill（由 Router 对字面 `unknown` 也返回 `unknown_intent`）。

- [ ] **Step 5: Commit** → `feat: add skill registry and router`

---

