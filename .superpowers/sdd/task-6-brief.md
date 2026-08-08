### Task 6: SlotManager

**Files:**
- Create: `E:\AI-Skill-Platform\app\runtime\slot_manager.py`
- Create: `E:\AI-Skill-Platform\tests\test_slot_manager.py`

**Interfaces:**
- Produces: `SlotManager.missing(required: list[str], slots: dict) -> list[str]`（按 required 顺序；值为 `None` 或缺失算缺）

- [ ] **Step 1: 测试**

```python
from app.runtime.slot_manager import SlotManager

def test_missing_slots_ordered():
    m = SlotManager()
    assert m.missing(["text", "date"], {}) == ["text", "date"]
    assert m.missing(["text", "date"], {"text": "x"}) == ["date"]
    assert m.missing(["text"], {"text": "x"}) == []
```

- [ ] **Step 2–4: 实现并通过**

```python
class SlotManager:
    def missing(self, required: list[str], slots: dict) -> list[str]:
        out = []
        for name in required:
            if name not in slots or slots[name] is None or slots[name] == "":
                out.append(name)
        return out
```

- [ ] **Step 5: Commit** → `feat: add slot manager`

---

