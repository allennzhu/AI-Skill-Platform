# AI Skill Platform

FastAPI agent shell with LLM-driven chat and direct skill execution.

## Requirements

- Python 3.11+
- Optional: local Ollama (or compatible OpenAI API) for `/v1/chat`

## Install

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # edit LLM settings if needed
```

## Start

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Or use values from `.env` (defaults shown in `.env.example`).

## API examples

### Health

```bash
curl -s http://127.0.0.1:8000/health
```

Expected: `{"status":"ok"}`

### Execute — echo

```bash
curl -s -X POST http://127.0.0.1:8000/v1/execute \
  -H "Content-Type: application/json" \
  -d "{\"intent\":\"echo\",\"slots\":{\"text\":\"hi\"}}"
```

### Execute — health skill

```bash
curl -s -X POST http://127.0.0.1:8000/v1/execute \
  -H "Content-Type: application/json" \
  -d "{\"intent\":\"health\",\"slots\":{}}"
```

### Chat (requires local LLM)

Ensure Ollama (or configured endpoint) is running with `deepseek-r1` or your `LLM_MODEL`.

```bash
curl -s -X POST http://127.0.0.1:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"把 text 设为 hello 并 echo\"}"
```

## Tests

```bash
pytest -v
```

## Optional manual smoke (local LLM)

After starting the server, run the health and execute curls above, then the chat curl. Skip chat if the LLM endpoint is unavailable.
