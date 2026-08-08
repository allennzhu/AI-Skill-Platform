# Task 1 Report: 工程脚手架 + `/health`

## Status

**DONE** — FastAPI 脚手架与 `GET /health` 已按 brief 实现，TDD RED→GREEN 完成，测试通过，已提交。

## Scope

- 创建 `requirements.txt`、`pytest.ini`、目录结构与空 `__init__.py`
- 实现 `Settings` / `get_settings()`（`app/config.py`）
- 实现 `create_app() -> FastAPI` 与 `GET /health` → `{"status":"ok"}`
- TDD：先写失败测试，再最小实现
- 未实现 Task 2+ 内容

## TDD Evidence

### Step 3 — RED（预期失败）

**命令**（Windows 使用 `py` 替代不可用的 `python`）：

```powershell
cd E:\AI-Skill-Platform
py -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\pytest tests\test_health.py -v
```

**结果**：`ModuleNotFoundError: No module named 'app.main'`（collection error，exit code 2）

```
tests\test_health.py:2: in <module>
    from app.main import create_app
E   ModuleNotFoundError: No module named 'app.main'
```

### Step 5 — GREEN（预期通过）

**命令**：

```powershell
E:\AI-Skill-Platform\.venv\Scripts\pytest tests\test_health.py -v
```

**结果**：1 passed（exit code 0）

```
tests/test_health.py::test_health_returns_ok PASSED                      [100%]
======================== 1 passed, 1 warning in 0.20s =========================
```

**DeprecationWarning**：FastAPI TestClient 提示 `httpx` 与 starlette testclient 的兼容性警告；brief 未要求处理，不影响功能。

## Files Created

| Path | Purpose |
|------|---------|
| `requirements.txt` | 依赖（与 brief  verbatim） |
| `pytest.ini` | pytest 配置 |
| `.gitignore` | 忽略 `.venv/`、`__pycache__/` 等（见 Concerns） |
| `app/__init__.py` | 包标记 |
| `app/config.py` | `Settings` + `get_settings()` |
| `app/main.py` | `create_app()` + 模块级 `app` |
| `app/api/__init__.py` | 包标记 |
| `app/api/v1/__init__.py` | 包标记 |
| `app/api/v1/health.py` | `GET /health` 路由 |
| `tests/conftest.py` | 共享 fixture 占位 |
| `tests/test_health.py` | health 端点测试 |

## Interfaces Delivered

| Interface | Location | Notes |
|-----------|----------|-------|
| `create_app() -> FastAPI` | `app/main.py` | title `"AI Skill Platform"` |
| `Settings` | `app/config.py` | `host`, `port`, `llm_*`, `session_ttl_seconds` |
| `get_settings() -> Settings` | `app/config.py` | 工厂函数 |
| `GET /health` | `app/api/v1/health.py` | 返回 `{"status":"ok"}` |

## Commits

| SHA | Subject |
|-----|---------|
| `5b5d090` | feat: scaffold FastAPI app with /health |
| `9aee1e4` | chore: add gitignore and untrack pycache |
| `7226dd2` | chore: remove remaining tracked __pycache__ from index |

> 基线：`c2ee94a chore: init empty repository`（未 amend）

## Self-Review

### Matches brief

- 目录结构、依赖版本、pytest 配置与 brief 一致
- `config.py`、`health.py`、`main.py`、`conftest.py`、`test_health.py` 内容与 brief 代码块一致
- 仅实现 Task 1，无 Task 2+ 越界代码

### Deviations / extras

1. **`.gitignore` 额外提交**：首次 `git add app tests` 时 pytest 已生成 `__pycache__/*.pyc` 并被误纳入首 commit；追加 `.gitignore` 并从索引移除 pycache（`9aee1e4`）。brief 未要求 `.gitignore`，但为仓库卫生所必需。
2. **`python` vs `py`**：系统 PATH 无 `python`，venv 与 pytest 均通过 Windows `py` launcher 创建/运行；功能等价。

### Potential follow-ups (out of scope)

- `Settings` / `get_settings()` 尚未被 `main.py` 引用（brief 仅要求创建，Task 2+ 可能接入）
- FastAPI TestClient 的 httpx deprecation warning
- 可考虑在 brief 后续任务中补充 `.gitignore` 为正式步骤

## Test Summary

```
1 passed in 0.20s — tests/test_health.py::test_health_returns_ok
```

## Concerns

- 首 commit 曾短暂包含 `__pycache__`，已通过 follow-up commit 清理；当前 tree 干净。
- Windows 环境需使用 `py` 而非 `python` 创建 venv。

---

## Review Fix (Important Finding #1)

**Date**: 2026-07-31  
**Status**: FIXED

### Issue

Code review 发现 `app/api/**/__pycache__/*.pyc` 仍被 git 跟踪（`9aee1e4` 仅清理了部分路径）。

### Fix

1. 确认 `.gitignore` 已覆盖 `__pycache__/` 与 `*.py[cod]`（无需修改）。
2. 从索引移除剩余 3 个 `.pyc` 文件（`git rm --cached`，未删除工作区文件）：
   - `app/api/__pycache__/__init__.cpython-314.pyc`
   - `app/api/v1/__pycache__/__init__.cpython-314.pyc`
   - `app/api/v1/__pycache__/health.cpython-314.pyc`
3. 新 commit（未 squash/rewrite history）：`7226dd2` — `chore: remove remaining tracked __pycache__ from index`
4. 验证：`git ls-files` 无 `__pycache__` / `.pyc` 跟踪项。

### Post-Fix Test

**命令**：

```powershell
E:\AI-Skill-Platform\.venv\Scripts\pytest tests\test_health.py -v
```

**结果**：1 passed（exit code 0）

```
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0 -- E:\AI-Skill-Platform\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: E:\AI-Skill-Platform
configfile: pytest.ini
plugins: anyio-4.14.2, asyncio-1.4.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 1 item

tests/test_health.py::test_health_returns_ok PASSED                      [100%]

============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  E:\AI-Skill-Platform\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 1 passed, 1 warning in 0.18s =========================
```
