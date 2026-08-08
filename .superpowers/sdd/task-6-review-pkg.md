# Review package: b1229da74ff3aa938278fdbe834ce197af0c1d72..b19b47bb4b4039f184a709fc18b1ae10406f30ea
## Commits
b19b47b feat: add slot manager

## Files changed
 app/runtime/slot_manager.py | 7 +++++++
 tests/test_slot_manager.py  | 8 ++++++++
 2 files changed, 15 insertions(+)

## Diff
diff --git a/app/runtime/slot_manager.py b/app/runtime/slot_manager.py
new file mode 100644
index 0000000..23d3b9d
--- /dev/null
+++ b/app/runtime/slot_manager.py
@@ -0,0 +1,7 @@
+class SlotManager:
+    def missing(self, required: list[str], slots: dict) -> list[str]:
+        out = []
+        for name in required:
+            if name not in slots or slots[name] is None or slots[name] == "":
+                out.append(name)
+        return out
diff --git a/tests/test_slot_manager.py b/tests/test_slot_manager.py
new file mode 100644
index 0000000..326142d
--- /dev/null
+++ b/tests/test_slot_manager.py
@@ -0,0 +1,8 @@
+from app.runtime.slot_manager import SlotManager
+
+
+def test_missing_slots_ordered():
+    m = SlotManager()
+    assert m.missing(["text", "date"], {}) == ["text", "date"]
+    assert m.missing(["text", "date"], {"text": "x"}) == ["date"]
+    assert m.missing(["text"], {"text": "x"}) == []

