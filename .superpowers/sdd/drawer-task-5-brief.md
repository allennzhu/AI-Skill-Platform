### Task 5: 联调验收与文档勾选

**Files:**
- Modify: `E:\AI-Skill-Platform\.env`（本地 CORS_ORIGINS 含前端实际 origin，常见 `http://localhost:8080`）
- Modify: `E:\AI-Skill-Platform-Docs-v1\roadmap.md`（Phase5 前端项勾选进度）

- [ ] **Step 1: 确认 Agent 已重启并带 CORS**

- [ ] **Step 2: 浏览器验收清单**

1. FAB 可见，抽屉打开  
2. 发送「把 text 设为 hello 并 echo」→ 有 reply；详情可见 status/intent  
3. 多轮后 session 保持  
4. 新会话后旧 session_id 不再发送  
5. 历史可切换；刷新页面当前会话仍在  
6. Network 面板无 CORS 报错  

- [ ] **Step 3: 更新 roadmap 勾选说明**

- [ ] **Step 4: Commit 文档（若有 git）**

---

## Self-Review

| Spec 项 | Task |
|---------|------|
| 全局悬浮 + 抽屉 | Task 3–4 |
| VUE_APP_AGENT_API 直连 chat | Task 2–3 |
| 调试详情 / 快捷示例 / 新会话 / 历史 | Task 3–4 |
| localStorage 键与上限 20 | Task 2 |
| Agent CORS | Task 1 |
| 不改路由菜单、无鉴权 | 全局约束 |

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-31-51pm-ai-assistant-drawer.md`.

**两种执行方式：**

1. **Subagent-Driven（推荐）** — 每 Task 独立子代理 + 审查  
2. **Inline Execution** — 本会话连续执行  

选哪一种？
