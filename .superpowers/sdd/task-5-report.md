# Task 5 Report: Registry + Router

## Status

**DONE** — `SkillRegistry` 与 `Router` 已实现，扫描 `app/skills` 下含 `manifest.yaml` 的包并注册；字面 intent `"unknown"` 不注册且路由时返回 `unknown_intent`。TDD 完成，全量 9 项测试通过，已提交。

## Scope

- 创建 `app/runtime/registry.py`（`RegisteredSkill`、`SkillRegistry.load_dir/get/list_intents`）
- 创建 `app/runtime/router.py`（`Router.resolve`，失败 raise `AppError(code="unknown_intent")`）
- 创建 `tests/test_registry.py`（含 brief 用例 + 字面 `unknown` 用例）

## TDD Evidence

### Step 1 — RED（预期）

brief 要求先写测试；实现前 `test_registry.py` 会因模块缺失 collection error。

### Step 4 — GREEN

**命令**：

```powershell
E:\AI-Skill-Platform\.venv\Scripts\pytest tests\ -v
```

**结果**：9 passed（exit code 0）

```
tests/test_registry.py::test_registry_loads_echo_and_health PASSED
tests/test_registry.py::test_router_unknown_intent PASSED
tests/test_registry.py::test_router_literal_unknown_intent PASSED
```

## Files Created

| Path | Purpose |
|------|---------|
| `app/runtime/registry.py` | 扫描注册 skill 包，跳过 intent `"unknown"` |
| `app/runtime/router.py` | 按 intent 解析 `RegisteredSkill` |
| `tests/test_registry.py` | registry / router 单元测试 |

## Interfaces Delivered

| Interface | Location | Notes |
|-----------|----------|-------|
| `RegisteredSkill` | `app/runtime/registry.py` | manifest + skill |
| `SkillRegistry.load_dir` | `app/runtime/registry.py` | 扫描子目录 manifest.yaml |
| `SkillRegistry.get` | `app/runtime/registry.py` | 按 intent 查找 |
| `SkillRegistry.list_intents` | `app/runtime/registry.py` | 已注册 intent 列表 |
| `Router.resolve` | `app/runtime/router.py` | 未知 intent → `AppError(unknown_intent)` |

## Commits

| SHA | Subject |
|-----|---------|
| `b1229da` | feat: add skill registry and router |

> 基线：`e873edf feat: add echo and health placeholder skills`

## Concerns

1. **health skills 列表仍硬编码**：`health` executor 内 `["echo", "health"]` 未接 Registry；Task 6+ 可改为 `registry.list_intents()`。
2. **无重复 intent 冲突检测**：后扫描包会覆盖同 intent 条目；当前仅 echo/health，风险低。
3. **未接线 RuntimeService**：Registry/Router 仅单元级可用，Task 7 orchestrator 待接入。

## Test Summary

| Suite | Count | Result |
|-------|-------|--------|
| `tests/test_registry.py` | 3 | PASS |
| Full `tests/` | 9 | PASS |
