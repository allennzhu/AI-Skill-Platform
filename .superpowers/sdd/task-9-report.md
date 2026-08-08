# Task 9 Report: LLM JSON 解析 + HttpLLMClient

## Status

已实现 LLM 意图 JSON 解析、系统提示词构建及 HTTP/Fake 客户端；未接入 chat API。

## Changes

- 新增 `parse_intent_json`，支持纯 JSON 与 Markdown 围栏，并将无效响应转换为 `llm_error`。
- 新增 `build_system_prompt`，约束模型只返回意图与槽位 JSON。
- 新增 `LLMClient` Protocol、`HttpLLMClient` 和 `FakeLLMClient`。
- 新增解析器测试，覆盖纯 JSON、围栏 JSON 和非法内容。

## Verification

- TDD 红灯：测试收集因 `app.llm` 尚不存在而失败。
- Focused: 3 passed (`test_llm_parse.py`)。
- Full suite: 24 passed, 1 个既有 Starlette/httpx 弃用警告。
- Commit: `343ea9b feat: add LLM client and JSON parser`。
