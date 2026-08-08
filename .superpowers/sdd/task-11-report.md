# Task 11 Report

## Done
- `.env.example` — HOST/PORT/LLM_*/SESSION_TTL_SECONDS per brief
- `README.md` — install, uvicorn start, curl for health / execute (echo+health) / chat
- `pytest -v` — **29 passed**
- `roadmap.md` — Phase1 & Phase2 items marked complete (docs repo, no git)

## Commit
- `docs: add README and env example` on `feature/agent-shell`

## Optional smoke (manual)
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
curl -s http://127.0.0.1:8000/health
curl -s -X POST http://127.0.0.1:8000/v1/execute -H "Content-Type: application/json" -d "{\"intent\":\"echo\",\"slots\":{\"text\":\"hi\"}}"
curl -s -X POST http://127.0.0.1:8000/v1/chat -H "Content-Type: application/json" -d "{\"message\":\"把 text 设为 hello 并 echo\"}"
```
Chat curl skipped if local LLM unavailable; automated tests cover chat via FakeLLMClient.
