# 飞书工作总结机器人 — Agent 侧补充

> 日期：2026-08-14  
> 主规格：51PM `docs/superpowers/specs/2026-08-14-feishu-work-summary-bot-design.md`

飞书编排在 51PM。Agent 仅两处改动：

1. `POST /internal_api/ai_api_key/resolve` 增加 `user_id`（与 `oauth_token` 二选一）。
2. `POST /v1/execute` 允许 51PM 用 `X-Internal-Secret` + `X-Internal-User-Id` 代替用户 Bearer。

skill 仍是 `work_hours_ai_summary`，入参 `context` 由 51PM 装配。
