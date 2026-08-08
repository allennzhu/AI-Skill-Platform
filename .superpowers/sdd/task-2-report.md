# Task 2 Report: API 模型与错误处理

## Status

**DONE** — Pydantic 请求/响应模型、`RuntimeResult` dataclass、`AppError` 与异常 handler 已按 brief 实现，TDD RED→GREEN 完成，全量测试通过，已提交。

## Scope

- 创建 `app/models/api.py`（`ChatRequest`、`ExecuteRequest`、`AgentResponse`）
- 创建 `app/models/runtime.py`（`RuntimeResult` dataclass）
- 创建 `app/api/errors.py`（`AppError`、`register_exception_handlers`）
- 修改 `app/main.py` 在 `create_app()` 中注册异常 handler
- TDD：先写失败测试，再最小实现
- 未实现 Task 3+ 内容

## TDD Evidence

### Step 2 — RED（预期失败）

**命令**：

```powershell
E:\AI-Skill-Platform\.venv\Scripts\pytest tests/test_errors.py -v
```

**结果**：`ModuleNotFoundError: No module named 'app.api.errors'`（collection error，exit code 2）

```
tests\test_errors.py:3: in <module>
    from app.api.errors import AppError, register_exception_handlers
E   ModuleNotFoundError: No module named 'app.api.errors'
```

### Step 4 — GREEN（预期通过）

**命令**：

```powershell
E:\AI-Skill-Platform\.venv\Scripts\pytest tests/ -v
```

**结果**：2 passed（exit code 0）

```
tests/test_errors.py::test_app_error_shape PASSED                        [ 50%]
tests/test_health.py::test_health_returns_ok PASSED                      [100%]
======================== 2 passed, 1 warning in 0.21s =========================
```

**DeprecationWarning**：FastAPI TestClient 提示 `httpx` 与 starlette testclient 的兼容性警告；brief 未要求处理，不影响功能。

## Files Created / Modified

| Path | Action | Purpose |
|------|--------|---------|
| `app/models/__init__.py` | Create | 包标记（空） |
| `app/models/api.py` | Create | Pydantic 请求/响应模型 |
| `app/models/runtime.py` | Create | `RuntimeResult` dataclass |
| `app/api/errors.py` | Create | `AppError` + `register_exception_handlers` |
| `app/main.py` | Modify | 调用 `register_exception_handlers(app)` |
| `tests/test_errors.py` | Create | `AppError` JSON 响应形状测试 |

## Interfaces Delivered

| Interface | Location | Notes |
|-----------|----------|-------|
| `ChatRequest` | `app/models/api.py` | `message: str`, `session_id: Optional[str]` |
| `ExecuteRequest` | `app/models/api.py` | `intent`, `slots` (default `{}`), `session_id` |
| `AgentResponse` | `app/models/api.py` | 业务字段 + 可选字段默认 `None` / 空集合 |
| `RuntimeResult` | `app/models/runtime.py` | dataclass，字段与 `AgentResponse` 对齐 |
| `AppError` | `app/api/errors.py` | `code`, `message`, `details`, `status_code=400` |
| `register_exception_handlers` | `app/api/errors.py` | 返回 `{"error": {code, message, details}}` JSON |

## Commits

| SHA | Subject |
|-----|---------|
| `622bc1b` | feat: add API models and AppError handler |

> 基线：`7226dd2 chore: remove remaining tracked __pycache__ from index`

## Self-Review

### Matches brief

- 所有代码块与 brief verbatim 一致（含 `Field(default_factory=...)` 避免可变默认值陷阱）
- `create_app()` 在 include router 之前注册 handler
- 测试用例与 brief 完全一致
- 仅实现 Task 2，无 Task 3+ 越界代码
- 未提交 `__pycache__` 或 `.venv`

### Deviations / extras

无。实现严格遵循 brief。

### Potential follow-ups (out of scope)

- `ChatRequest` / `ExecuteRequest` / `AgentResponse` / `RuntimeResult` 尚未被路由或 runtime 引用（Task 3+ 接入）
- 未添加模型序列化/反序列化的单元测试（brief 仅要求 error handler 测试）
- `AppError` 自定义 `status_code` 未单独测试（brief 测试用默认 400）
- FastAPI TestClient 的 httpx deprecation warning

## Test Summary

```
2 passed in 0.21s
  tests/test_errors.py::test_app_error_shape
  tests/test_health.py::test_health_returns_ok
```

## Concerns

- 无阻塞性问题。
- `app/models/__init__.py` 为空，未 re-export 模型；后续任务可按需补充。
- Windows 环境 pytest 路径：`E:\AI-Skill-Platform\.venv\Scripts\pytest`。
