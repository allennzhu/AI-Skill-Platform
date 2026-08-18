# 飞书会议纪要 → 会议动态 — Agent 侧补充

> 日期：2026-08-18  
> 主规格：51PM `docs/superpowers/specs/2026-08-18-feishu-meeting-moment-design.md`

本期 **不新增 skill**。51PM 读出纪要正文后调用已有：

`POST /v1/execute`  `intent=moment_meeting_ai_fill`  
Header 与总结相同：`X-Internal-Secret` + `X-Internal-User-Id`

Slots：`raw_text`（必填）、`meet_types`、`known_users`。

飞书绑定、读文档、写 `AddMoment` 均在 51PM；群 @ 在识别为纪要来源后 **不走** `/v1/route`。
