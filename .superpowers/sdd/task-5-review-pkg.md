# Review package: e873edf57d2bc4895629b3d90484447adc6b9e89..b1229da74ff3aa938278fdbe834ce197af0c1d72
## Commits
b1229da feat: add skill registry and router

## Files changed
 app/runtime/registry.py | 39 +++++++++++++++++++++++++++++++++++++++
 app/runtime/router.py   | 17 +++++++++++++++++
 tests/test_registry.py  | 30 ++++++++++++++++++++++++++++++
 3 files changed, 86 insertions(+)

## Diff
diff --git a/app/runtime/registry.py b/app/runtime/registry.py
new file mode 100644
index 0000000..41fe884
--- /dev/null
+++ b/app/runtime/registry.py
@@ -0,0 +1,39 @@
+from __future__ import annotations
+
+from dataclasses import dataclass
+from pathlib import Path
+
+from app.skills.base import Skill, SkillManifest, load_skill_package
+
+
+@dataclass
+class RegisteredSkill:
+    manifest: SkillManifest
+    skill: Skill
+
+
+class SkillRegistry:
+    def __init__(self, skills: dict[str, RegisteredSkill] | None = None) -> None:
+        self._skills = skills or {}
+
+    @classmethod
+    def load_dir(cls, skills_root: Path) -> SkillRegistry:
+        skills: dict[str, RegisteredSkill] = {}
+        root = skills_root.resolve()
+        for child in sorted(root.iterdir()):
+            if not child.is_dir():
+                continue
+            manifest_path = child / "manifest.yaml"
+            if not manifest_path.is_file():
+                continue
+            manifest, skill = load_skill_package(child)
+            if manifest.intent == "unknown":
+                continue
+            skills[manifest.intent] = RegisteredSkill(manifest=manifest, skill=skill)
+        return cls(skills)
+
+    def get(self, intent: str) -> RegisteredSkill | None:
+        return self._skills.get(intent)
+
+    def list_intents(self) -> list[str]:
+        return sorted(self._skills.keys())
diff --git a/app/runtime/router.py b/app/runtime/router.py
new file mode 100644
index 0000000..2375741
--- /dev/null
+++ b/app/runtime/router.py
@@ -0,0 +1,17 @@
+from __future__ import annotations
+
+from app.api.errors import AppError
+from app.runtime.registry import RegisteredSkill, SkillRegistry
+
+
+class Router:
+    def __init__(self, registry: SkillRegistry) -> None:
+        self._registry = registry
+
+    def resolve(self, intent: str) -> RegisteredSkill:
+        if intent == "unknown":
+            raise AppError(code="unknown_intent", message=f"Unknown intent: {intent}")
+        registered = self._registry.get(intent)
+        if registered is None:
+            raise AppError(code="unknown_intent", message=f"Unknown intent: {intent}")
+        return registered
diff --git a/tests/test_registry.py b/tests/test_registry.py
new file mode 100644
index 0000000..8d6086b
--- /dev/null
+++ b/tests/test_registry.py
@@ -0,0 +1,30 @@
+from pathlib import Path
+
+import pytest
+
+from app.api.errors import AppError
+from app.runtime.registry import SkillRegistry
+from app.runtime.router import Router
+
+ROOT = Path(__file__).resolve().parents[1] / "app" / "skills"
+
+
+def test_registry_loads_echo_and_health():
+    reg = SkillRegistry.load_dir(ROOT)
+    assert set(reg.list_intents()) >= {"echo", "health"}
+
+
+def test_router_unknown_intent():
+    reg = SkillRegistry.load_dir(ROOT)
+    router = Router(reg)
+    with pytest.raises(AppError) as ei:
+        router.resolve("nope")
+    assert ei.value.code == "unknown_intent"
+
+
+def test_router_literal_unknown_intent():
+    reg = SkillRegistry.load_dir(ROOT)
+    router = Router(reg)
+    with pytest.raises(AppError) as ei:
+        router.resolve("unknown")
+    assert ei.value.code == "unknown_intent"

