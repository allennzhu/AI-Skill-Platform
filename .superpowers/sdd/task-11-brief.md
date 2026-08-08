### Task 11: `.env.example` + README + 手工冒烟清单

**Files:**
- Create: `E:\AI-Skill-Platform\.env.example`
- Create: `E:\AI-Skill-Platform\README.md`
- Modify: docs roadmap checkboxes 可选（文档仓）

**Interfaces:**
- Produces: 可运行说明

- [ ] **Step 1: 写入 `.env.example`**

```text
HOST=0.0.0.0
PORT=8000
LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=deepseek-r1
SESSION_TTL_SECONDS=3600
```

- [ ] **Step 2: 写入 README**（安装、启动、`curl` 示例：health / execute echo / execute health / chat）

- [ ] **Step 3: 跑全量测试**

Run: `pytest -v`  
Expected: 全部 PASS

- [ ] **Step 4: 本地 LLM 手工冒烟（人工）**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
curl -s http://127.0.0.1:8000/health
curl -s -X POST http://127.0.0.1:8000/v1/execute -H "Content-Type: application/json" -d "{\"intent\":\"echo\",\"slots\":{\"text\":\"hi\"}}"
curl -s -X POST http://127.0.0.1:8000/v1/chat -H "Content-Type: application/json" -d "{\"message\":\"把 text 设为 hello 并 echo\"}"
```

- [ ] **Step 5: Commit** → `docs: add README and env example`

- [ ] **Step 6: 更新文档仓 roadmap** 将 Phase1/2 对应勾选为进行中/完成（实现完成后）

---

## Self-Review

| Spec 项 | Task |
|---------|------|
| `GET /health` | Task 1 |
| 错误体 / AppError | Task 2 |
| Session 内存 + TTL | Task 3 |
| echo / health Skill + manifest | Task 4 |
| Registry / Router | Task 5 |
| SlotManager | Task 6 |
| Executor + Runtime 统一管线 | Task 7 |
| `POST /v1/execute` | Task 8 |
| LLM JSON / DeepSeek 客户端 | Task 9 |
| `POST /v1/chat` 双入口汇合 | Task 10 |
| 配置 / README / 测试最低线 | Task 11 |
| 无鉴权/无前端/无 Go API | 全局约束，无额外任务 |

已消除占位符；`RuntimeResult.status` 与 HTTP 200 同形策略在 Task 7/10 一致；`unknown` intent 不注册 Skill。

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-31-agent-platform-shell.md`.

**两种执行方式：**

1. **Subagent-Driven（推荐）** — 每 Task 派独立子代理，Task 间审查，迭代快  
2. **Inline Execution** — 本会话按 executing-plans 连续执行，设检查点  

选哪一种？
