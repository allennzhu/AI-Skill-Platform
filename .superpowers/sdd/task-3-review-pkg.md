# Review package: 622bc1b3aece849fed065d0a79dfd7eb0b701243..fe39d2840e0b51d28fb9a0b3280998caff02cfbe
## Commits
fe39d28 feat: add in-memory session store

## Files changed
 app/runtime/__init__.py |  0
 app/runtime/session.py  | 47 +++++++++++++++++++++++++++++++++++++++++++++++
 tests/test_session.py   | 25 +++++++++++++++++++++++++
 3 files changed, 72 insertions(+)

## Diff
diff --git a/app/runtime/__init__.py b/app/runtime/__init__.py
new file mode 100644
index 0000000..e69de29
diff --git a/app/runtime/session.py b/app/runtime/session.py
new file mode 100644
index 0000000..c6aa925
--- /dev/null
+++ b/app/runtime/session.py
@@ -0,0 +1,47 @@
+from __future__ import annotations
+
+import time
+import uuid
+from dataclasses import dataclass, field
+from typing import Any, Optional
+
+
+@dataclass
+class SessionData:
+    session_id: str
+    intent: Optional[str] = None
+    slots: dict[str, Any] = field(default_factory=dict)
+    updated_at: float = field(default_factory=time.time)
+
+
+class SessionStore:
+    def __init__(self, ttl_seconds: int = 3600):
+        self.ttl_seconds = ttl_seconds
+        self._data: dict[str, SessionData] = {}
+
+    def create(self, session_id: Optional[str] = None) -> SessionData:
+        sid = session_id or str(uuid.uuid4())
+        data = SessionData(session_id=sid)
+        self._data[sid] = data
+        return data
+
+    def get(self, session_id: str) -> Optional[SessionData]:
+        data = self._data.get(session_id)
+        if data is None:
+            return None
+        if time.time() - data.updated_at > self.ttl_seconds:
+            self._data.pop(session_id, None)
+            return None
+        return data
+
+    def save(self, data: SessionData) -> None:
+        self._data[data.session_id] = data
+
+    def merge_slots(
+        self, data: SessionData, intent: Optional[str], slots: dict[str, Any]
+    ) -> SessionData:
+        if intent:
+            data.intent = intent
+        data.slots.update(slots or {})
+        data.updated_at = time.time()
+        return data
diff --git a/tests/test_session.py b/tests/test_session.py
new file mode 100644
index 0000000..9322708
--- /dev/null
+++ b/tests/test_session.py
@@ -0,0 +1,25 @@
+import time
+from app.runtime.session import SessionStore
+
+
+def test_create_and_merge_slots():
+    store = SessionStore(ttl_seconds=60)
+    s = store.create()
+    assert s.session_id
+    s = store.merge_slots(s, intent="echo", slots={"text": "a"})
+    s = store.merge_slots(s, intent="echo", slots={"text": "b", "extra": 1})
+    assert s.slots == {"text": "b", "extra": 1}
+    assert s.intent == "echo"
+    store.save(s)
+    loaded = store.get(s.session_id)
+    assert loaded is not None
+    assert loaded.slots["text"] == "b"
+
+
+def test_expired_session_returns_none():
+    store = SessionStore(ttl_seconds=1)
+    s = store.create()
+    store.save(s)
+    s.updated_at = time.time() - 10
+    store.save(s)
+    assert store.get(s.session_id) is None

