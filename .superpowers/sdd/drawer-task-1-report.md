# Task 1 Report: Agent CORS

**Branch:** `feature/agent-shell`  
**Date:** 2026-07-31  
**Status:** Complete

## Summary

Added configurable CORS support so the 51pm frontend agent drawer can call the FastAPI backend from browser origins (e.g. `http://localhost:8080`). Implemented via TDD: failing test first, then `Settings.cors_origins` + `CORSMiddleware` in `create_app`.

## Changes

| File | Change |
|------|--------|
| `app/config.py` | Added `cors_origins: str` with default `http://localhost:8080,http://127.0.0.1:8080` |
| `app/main.py` | Registered `CORSMiddleware` after app creation; parses comma-separated origins |
| `.env.example` | Documented `CORS_ORIGINS=...` |
| `tests/test_cors.py` | New test: OPTIONS `/health` with allowed Origin returns `access-control-allow-origin` |

## TDD Steps

1. **Red** — `tests/test_cors.py::test_cors_allows_configured_origin` failed (no CORS header, 405 on OPTIONS).
2. **Green** — Implementation added; CORS test passes.
3. **Commit** — `feat: add configurable CORS for frontend agent access`

## Test Results

```
tests/test_cors.py::test_cors_allows_configured_origin PASSED
```

Full suite: **37 passed, 1 failed** (pre-existing).

- **Failed (unrelated):** `tests/test_llm_client.py::test_llm_timeout_defaults_to_120_seconds` — local `.env` sets `LLM_TIMEOUT_SECONDS=300`, overriding the code default of 120. Not introduced by this task.

## Implementation Notes

- `get_settings()` returns a fresh `Settings()` on each call (no `lru_cache`), so `monkeypatch.setenv("CORS_ORIGINS", ...)` before `create_app()` works in tests without cache clearing.
- Middleware config: `allow_credentials=True`, `allow_methods=["*"]`, `allow_headers=["*"]`.
- Origins parsed with strip/filter on comma split to tolerate whitespace in env values.

## Verification Commands

```powershell
E:\AI-Skill-Platform\.venv\Scripts\pytest tests\test_cors.py -v
E:\AI-Skill-Platform\.venv\Scripts\pytest -v
```

## Commit

```
feat: add configurable CORS for frontend agent access
```

Files: `app/config.py`, `app/main.py`, `.env.example`, `tests/test_cors.py`

## Concerns / Follow-ups

- None for CORS scope. Frontend integration is Task 2+ per drawer plan.
- Consider isolating settings tests from developer `.env` (e.g. `monkeypatch` or test-specific env) to avoid flaky `test_llm_timeout_defaults_to_120_seconds` in local runs.

## Out of Scope (per brief)

- No frontend changes.
- No additional CORS tests (e.g. disallowed origin) unless requested in later tasks.
