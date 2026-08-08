# Review package: 3aef7e48281089669bc644f4d93f654a5886909b..db30df15fa483d003a9731a3946e465260284f36
## Commits
db30df1 docs: add README and env example

## Files changed
 .env.example |  6 +++++
 README.md    | 75 ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 2 files changed, 81 insertions(+)

## Diff
diff --git a/.env.example b/.env.example
new file mode 100644
index 0000000..bbc0b80
--- /dev/null
+++ b/.env.example
@@ -0,0 +1,6 @@
+HOST=0.0.0.0
+PORT=8000
+LLM_BASE_URL=http://127.0.0.1:11434/v1
+LLM_API_KEY=ollama
+LLM_MODEL=deepseek-r1
+SESSION_TTL_SECONDS=3600
diff --git a/README.md b/README.md
new file mode 100644
index 0000000..59420a4
--- /dev/null
+++ b/README.md
@@ -0,0 +1,75 @@
+# AI Skill Platform
+
+FastAPI agent shell with LLM-driven chat and direct skill execution.
+
+## Requirements
+
+- Python 3.11+
+- Optional: local Ollama (or compatible OpenAI API) for `/v1/chat`
+
+## Install
+
+```bash
+python -m venv .venv
+# Windows
+.venv\Scripts\activate
+# Linux / macOS
+source .venv/bin/activate
+
+pip install -r requirements.txt
+cp .env.example .env   # edit LLM settings if needed
+```
+
+## Start
+
+```bash
+uvicorn app.main:app --host 0.0.0.0 --port 8000
+```
+
+Or use values from `.env` (defaults shown in `.env.example`).
+
+## API examples
+
+### Health
+
+```bash
+curl -s http://127.0.0.1:8000/health
+```
+
+Expected: `{"status":"ok"}`
+
+### Execute 鈥?echo
+
+```bash
+curl -s -X POST http://127.0.0.1:8000/v1/execute \
+  -H "Content-Type: application/json" \
+  -d "{\"intent\":\"echo\",\"slots\":{\"text\":\"hi\"}}"
+```
+
+### Execute 鈥?health skill
+
+```bash
+curl -s -X POST http://127.0.0.1:8000/v1/execute \
+  -H "Content-Type: application/json" \
+  -d "{\"intent\":\"health\",\"slots\":{}}"
+```
+
+### Chat (requires local LLM)
+
+Ensure Ollama (or configured endpoint) is running with `deepseek-r1` or your `LLM_MODEL`.
+
+```bash
+curl -s -X POST http://127.0.0.1:8000/v1/chat \
+  -H "Content-Type: application/json" \
+  -d "{\"message\":\"鎶?text 璁句负 hello 骞?echo\"}"
+```
+
+## Tests
+
+```bash
+pytest -v
+```
+
+## Optional manual smoke (local LLM)
+
+After starting the server, run the health and execute curls above, then the chat curl. Skip chat if the LLM endpoint is unavailable.

