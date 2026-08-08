# Review package: a12824721d19f92a835afd6cceeb48940e91bede..343ea9b8035980d925ae5f753f42ecffc8c60f9b
## Commits
343ea9b feat: add LLM client and JSON parser

## Files changed
 app/llm/client.py       | 52 +++++++++++++++++++++++++++++++++++++++++++++++++
 app/llm/parse.py        | 39 +++++++++++++++++++++++++++++++++++++
 app/llm/prompt.py       |  9 +++++++++
 tests/test_llm_parse.py | 20 +++++++++++++++++++
 4 files changed, 120 insertions(+)

## Diff
diff --git a/app/llm/client.py b/app/llm/client.py
new file mode 100644
index 0000000..8530c54
--- /dev/null
+++ b/app/llm/client.py
@@ -0,0 +1,52 @@
+from collections.abc import Callable
+from typing import Protocol
+
+import httpx
+
+from app.api.errors import AppError
+from app.config import Settings
+
+
+class LLMClient(Protocol):
+    def complete(self, system: str, user: str) -> str: ...
+
+
+class HttpLLMClient:
+    def __init__(self, settings: Settings):
+        self.settings = settings
+
+    def complete(self, system: str, user: str) -> str:
+        try:
+            response = httpx.post(
+                f"{self.settings.llm_base_url.rstrip('/')}/chat/completions",
+                headers={"Authorization": f"Bearer {self.settings.llm_api_key}"},
+                json={
+                    "model": self.settings.llm_model,
+                    "messages": [
+                        {"role": "system", "content": system},
+                        {"role": "user", "content": user},
+                    ],
+                    "temperature": 0,
+                },
+            )
+            response.raise_for_status()
+            content = response.json()["choices"][0]["message"]["content"]
+            if not isinstance(content, str):
+                raise TypeError("LLM content must be a string")
+            return content
+        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
+            raise AppError(
+                code="llm_error",
+                message="LLM request failed",
+                status_code=502,
+            ) from exc
+
+
+class FakeLLMClient:
+    def __init__(self, scripted: str | Callable[[str, str], str]):
+        self.scripted = scripted
+
+    def complete(self, system: str, user: str) -> str:
+        if callable(self.scripted):
+            return self.scripted(system, user)
+        return self.scripted
diff --git a/app/llm/parse.py b/app/llm/parse.py
new file mode 100644
index 0000000..a58e51c
--- /dev/null
+++ b/app/llm/parse.py
@@ -0,0 +1,39 @@
+import json
+import re
+from typing import Any
+
+from app.api.errors import AppError
+
+
+_JSON_FENCE = re.compile(r"^\s*```(?:json)?\s*\n?(.*?)\n?\s*```\s*$", re.DOTALL | re.IGNORECASE)
+
+
+def parse_intent_json(text: str) -> dict[str, Any]:
+    match = _JSON_FENCE.match(text)
+    payload = match.group(1).strip() if match else text.strip()
+
+    try:
+        parsed = json.loads(payload)
+    except (json.JSONDecodeError, TypeError) as exc:
+        raise AppError(
+            code="llm_error",
+            message="LLM returned invalid JSON",
+            status_code=502,
+        ) from exc
+
+    if not isinstance(parsed, dict) or "intent" not in parsed:
+        raise AppError(
+            code="llm_error",
+            message="LLM response is missing intent",
+            status_code=502,
+        )
+
+    slots = parsed.get("slots", {})
+    if not isinstance(parsed["intent"], str) or not isinstance(slots, dict):
+        raise AppError(
+            code="llm_error",
+            message="LLM response has invalid intent or slots",
+            status_code=502,
+        )
+
+    return {"intent": parsed["intent"], "slots": slots}
diff --git a/app/llm/prompt.py b/app/llm/prompt.py
new file mode 100644
index 0000000..16298fc
--- /dev/null
+++ b/app/llm/prompt.py
@@ -0,0 +1,9 @@
+def build_system_prompt(intents_doc: str) -> str:
+    return (
+        "You route user messages to supported intents.\n"
+        "Return only a JSON object with this exact shape: "
+        '{"intent":"<intent name>","slots":{}}.\n'
+        "Do not include Markdown fences or explanatory text.\n\n"
+        "Supported intents:\n"
+        f"{intents_doc.strip()}"
+    )
diff --git a/tests/test_llm_parse.py b/tests/test_llm_parse.py
new file mode 100644
index 0000000..62fe03e
--- /dev/null
+++ b/tests/test_llm_parse.py
@@ -0,0 +1,20 @@
+import pytest
+
+from app.api.errors import AppError
+from app.llm.parse import parse_intent_json
+
+
+def test_parse_plain_json():
+    assert parse_intent_json('{"intent":"echo","slots":{"text":"x"}}')["intent"] == "echo"
+
+
+def test_parse_fenced_json():
+    raw = '```json\n{"intent":"echo","slots":{}}\n```'
+    assert parse_intent_json(raw)["slots"] == {}
+
+
+def test_parse_invalid():
+    with pytest.raises(AppError) as exc_info:
+        parse_intent_json("not json")
+
+    assert exc_info.value.code == "llm_error"

