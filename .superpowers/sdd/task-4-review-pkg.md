# Review package: fe39d2840e0b51d28fb9a0b3280998caff02cfbe..e873edf57d2bc4895629b3d90484447adc6b9e89
## Commits
e873edf feat: add echo and health placeholder skills

## Files changed
 app/skills/__init__.py          |  0
 app/skills/base.py              | 91 +++++++++++++++++++++++++++++++++++++++++
 app/skills/echo/executor.py     |  5 +++
 app/skills/echo/manifest.yaml   |  9 ++++
 app/skills/echo/normalizer.py   |  5 +++
 app/skills/echo/response.py     |  5 +++
 app/skills/echo/validator.py    |  7 ++++
 app/skills/health/executor.py   |  5 +++
 app/skills/health/manifest.yaml |  6 +++
 app/skills/health/normalizer.py |  5 +++
 app/skills/health/response.py   |  5 +++
 app/skills/health/validator.py  |  5 +++
 tests/test_skills_unit.py       | 23 +++++++++++
 13 files changed, 171 insertions(+)

## Diff
diff --git a/app/skills/__init__.py b/app/skills/__init__.py
new file mode 100644
index 0000000..e69de29
diff --git a/app/skills/base.py b/app/skills/base.py
new file mode 100644
index 0000000..e8e08e2
--- /dev/null
+++ b/app/skills/base.py
@@ -0,0 +1,91 @@
+from __future__ import annotations
+
+import importlib.util
+from dataclasses import dataclass
+from pathlib import Path
+from typing import Any, Protocol, runtime_checkable
+
+import yaml
+
+
+@dataclass
+class SkillManifest:
+    name: str
+    intent: str
+    description: str
+    required_slots: list[str]
+
+
+@runtime_checkable
+class Skill(Protocol):
+    def validate(self, slots: dict[str, Any]) -> None: ...
+
+    def normalize(self, slots: dict[str, Any]) -> dict[str, Any]: ...
+
+    def execute(self, slots: dict[str, Any]) -> dict[str, Any]: ...
+
+    def build_response(self, result: dict[str, Any]) -> dict[str, Any]: ...
+
+
+class _LoadedSkill:
+    def __init__(
+        self,
+        validator: Any,
+        normalizer: Any,
+        executor: Any,
+        response: Any,
+    ) -> None:
+        self._validator = validator
+        self._normalizer = normalizer
+        self._executor = executor
+        self._response = response
+
+    def validate(self, slots: dict[str, Any]) -> None:
+        self._validator.validate(slots)
+
+    def normalize(self, slots: dict[str, Any]) -> dict[str, Any]:
+        return self._normalizer.normalize(slots)
+
+    def execute(self, slots: dict[str, Any]) -> dict[str, Any]:
+        return self._executor.execute(slots)
+
+    def build_response(self, result: dict[str, Any]) -> dict[str, Any]:
+        return self._response.build_response(result)
+
+
+def _load_module(skill_dir: Path, module_name: str) -> Any:
+    path = skill_dir / f"{module_name}.py"
+    spec = importlib.util.spec_from_file_location(
+        f"skill.{skill_dir.name}.{module_name}",
+        path,
+    )
+    if spec is None or spec.loader is None:
+        raise ImportError(f"Cannot load skill module: {path}")
+    module = importlib.util.module_from_spec(spec)
+    spec.loader.exec_module(module)
+    return module
+
+
+def _parse_manifest(skill_dir: Path) -> SkillManifest:
+    manifest_path = skill_dir / "manifest.yaml"
+    with manifest_path.open(encoding="utf-8") as f:
+        data = yaml.safe_load(f)
+    required = data.get("slots", {}).get("required", [])
+    required_slots = [slot["name"] for slot in required]
+    return SkillManifest(
+        name=data["name"],
+        intent=data["intent"],
+        description=data["description"],
+        required_slots=required_slots,
+    )
+
+
+def load_skill_package(path: Path) -> tuple[SkillManifest, Skill]:
+    skill_dir = path.resolve()
+    manifest = _parse_manifest(skill_dir)
+    validator = _load_module(skill_dir, "validator")
+    normalizer = _load_module(skill_dir, "normalizer")
+    executor = _load_module(skill_dir, "executor")
+    response = _load_module(skill_dir, "response")
+    skill = _LoadedSkill(validator, normalizer, executor, response)
+    return manifest, skill
diff --git a/app/skills/echo/executor.py b/app/skills/echo/executor.py
new file mode 100644
index 0000000..b7348fa
--- /dev/null
+++ b/app/skills/echo/executor.py
@@ -0,0 +1,5 @@
+from typing import Any
+
+
+def execute(slots: dict[str, Any]) -> dict[str, Any]:
+    return {"echo": slots["text"]}
diff --git a/app/skills/echo/manifest.yaml b/app/skills/echo/manifest.yaml
new file mode 100644
index 0000000..d87fdb0
--- /dev/null
+++ b/app/skills/echo/manifest.yaml
@@ -0,0 +1,9 @@
+name: echo
+intent: echo
+description: Echo back the text slot
+slots:
+  required:
+    - name: text
+      type: string
+      description: Text to echo
+  optional: []
diff --git a/app/skills/echo/normalizer.py b/app/skills/echo/normalizer.py
new file mode 100644
index 0000000..0f5db73
--- /dev/null
+++ b/app/skills/echo/normalizer.py
@@ -0,0 +1,5 @@
+from typing import Any
+
+
+def normalize(slots: dict[str, Any]) -> dict[str, Any]:
+    return {"text": slots["text"]}
diff --git a/app/skills/echo/response.py b/app/skills/echo/response.py
new file mode 100644
index 0000000..12ced0e
--- /dev/null
+++ b/app/skills/echo/response.py
@@ -0,0 +1,5 @@
+from typing import Any
+
+
+def build_response(result: dict[str, Any]) -> dict[str, Any]:
+    return {"result": result, "reply": f"echo: {result['echo']}"}
diff --git a/app/skills/echo/validator.py b/app/skills/echo/validator.py
new file mode 100644
index 0000000..0d99e25
--- /dev/null
+++ b/app/skills/echo/validator.py
@@ -0,0 +1,7 @@
+from typing import Any
+
+
+def validate(slots: dict[str, Any]) -> None:
+    text = slots.get("text")
+    if text is None or not isinstance(text, str):
+        raise ValueError("text required")
diff --git a/app/skills/health/executor.py b/app/skills/health/executor.py
new file mode 100644
index 0000000..f648c9f
--- /dev/null
+++ b/app/skills/health/executor.py
@@ -0,0 +1,5 @@
+from typing import Any
+
+
+def execute(slots: dict[str, Any]) -> dict[str, Any]:
+    return {"runtime": "ok", "skills": ["echo", "health"]}
diff --git a/app/skills/health/manifest.yaml b/app/skills/health/manifest.yaml
new file mode 100644
index 0000000..4c58a56
--- /dev/null
+++ b/app/skills/health/manifest.yaml
@@ -0,0 +1,6 @@
+name: health
+intent: health
+description: Runtime health skill
+slots:
+  required: []
+  optional: []
diff --git a/app/skills/health/normalizer.py b/app/skills/health/normalizer.py
new file mode 100644
index 0000000..bff89b5
--- /dev/null
+++ b/app/skills/health/normalizer.py
@@ -0,0 +1,5 @@
+from typing import Any
+
+
+def normalize(slots: dict[str, Any]) -> dict[str, Any]:
+    return dict(slots)
diff --git a/app/skills/health/response.py b/app/skills/health/response.py
new file mode 100644
index 0000000..75d7175
--- /dev/null
+++ b/app/skills/health/response.py
@@ -0,0 +1,5 @@
+from typing import Any
+
+
+def build_response(result: dict[str, Any]) -> dict[str, Any]:
+    return {"result": result}
diff --git a/app/skills/health/validator.py b/app/skills/health/validator.py
new file mode 100644
index 0000000..34685aa
--- /dev/null
+++ b/app/skills/health/validator.py
@@ -0,0 +1,5 @@
+from typing import Any
+
+
+def validate(slots: dict[str, Any]) -> None:
+    return None
diff --git a/tests/test_skills_unit.py b/tests/test_skills_unit.py
new file mode 100644
index 0000000..b300133
--- /dev/null
+++ b/tests/test_skills_unit.py
@@ -0,0 +1,23 @@
+from pathlib import Path
+
+from app.skills.base import load_skill_package
+
+ROOT = Path(__file__).resolve().parents[1] / "app" / "skills"
+
+
+def test_echo_skill_executes():
+    manifest, skill = load_skill_package(ROOT / "echo")
+    assert manifest.intent == "echo"
+    assert manifest.required_slots == ["text"]
+    skill.validate({"text": "hi"})
+    slots = skill.normalize({"text": "hi"})
+    result = skill.execute(slots)
+    payload = skill.build_response(result)
+    assert payload["result"] == {"echo": "hi"}
+
+
+def test_health_skill_lists_skills():
+    _, skill = load_skill_package(ROOT / "health")
+    payload = skill.build_response(skill.execute({}))
+    assert payload["result"]["runtime"] == "ok"
+    assert "echo" in payload["result"]["skills"]

