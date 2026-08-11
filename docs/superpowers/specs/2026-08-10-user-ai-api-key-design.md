# 用户级 AI 大模型 API Key 配置与消费 — 设计规格

> 日期：2026-08-10  
> 状态：已确认（待实现）  
> 关联草案：桌面 `2026-08-10-AI大模型APIKey配置与消费方案.md`  
> 范围：**51PM 后端 + AI-Skill-Platform**；前端仅交付接口/联调文档，不实现页面与调用改造代码

---

## 1. 目标与非目标

### 1.1 目标

1. 用户可在 51PM 自助管理多条 OpenAI 兼容 API Key（加密存储），并指定一条「生效中」Key + 默认模型。
2. Agent Runtime（AI-Skill-Platform）处理 AI 请求时，消费**该用户自己的** Key，不再使用进程级全局共享 Key。
3. 未配置 / 未登录时明确失败（`no_api_key` / `unauthorized`），**严格无回退**到服务器 `.env` 全局 Key（含本地环境）。
4. 向前端交付配置类 API 文档 + 消费侧联调文档。

### 1.2 非目标（本次不做）

- 前端配置页、Workbench 入口、`executeSkill` 代码改造
- 团队/部门共享 Key、用量统计、按 AI 功能分 Key、多 Key 故障切换
- 全局 Key 开发回退开关

---

## 2. 架构（方案 A）

```
前端(+ Authorization: Bearer <oauthToken>)
  → 51PM POST /manage_api/ai_skill/execute | /chat
  → AI-Skill-Platform POST /v1/execute | /v1/chat（内网，转发同一 Bearer）
  → 51PM POST /internal_api/ai_api_key/resolve
       Header: X-Internal-Secret
       Body: { oauth_token }
  → 返回 { base_url, api_key, model }（解密后，仅服务间）
  → 用户自己的服务商 /chat/completions
```

| 系统 | 职责 |
|---|---|
| 51PM（Go） | CRUD、AES 加密落库、模型探测、内部 resolve、代理 Agent execute/chat |
| AI-Skill-Platform | 取 Bearer、调 resolve、按次构造 LLM 客户端、状态映射 |
| 前端 | 本次仅文档；只打 51PM，不直连 Agent |

**安全：**

- DB 只存密文 + 掩码；明文仅短暂存在于 `reveal` 与 `resolve` 响应内存中
- 禁止写入日志、`SessionStore`、会话 slots
- resolve 失败禁止 fallback 全局 `LLM_*`

---

## 3. 数据模型（51PM）

表名：`user_ai_api_key`

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | bigint PK | 自增 |
| `user_id` | int | 来自登录态 `uid`，禁止前端传入 |
| `provider_name` | varchar | 用户备注名 |
| `base_url` | varchar | OpenAI 兼容 Base URL |
| `api_key_encrypted` | text | `base64(nonce \|\| ciphertext \|\| tag)` AES-256-GCM |
| `api_key_mask` | varchar | 如 `sk-a1b2****9f3c` |
| `available_models` | json | 模型名数组 |
| `default_model` | varchar | 可空；手填或从列表选定 |
| `is_default` | tinyint | 同用户仅一条为 1 |
| `status` | varchar | `ok` / `invalid` |
| `last_verified_at` | datetime | 可空 |
| `created_at` / `updated_at` | datetime | — |

**业务规则：**

1. 首条创建自动 `is_default=true`。
2. `set_default`：同事务内将该用户其它记录置 0。
3. 删除当前生效记录且仍有剩余：自动将**剩余最新一条**（按 `id`/`updated_at` 最大）设为默认。
4. 创建/更新携带 `api_key`：先请求服务商校验；`/models` 探测失败**允许手填模型名**后仍可保存；HTTP 401 鉴权失败则**不落库**。
5. 列表接口只返回掩码，不返回明文。

**加密：**

- AES-256-GCM；主密钥配置项建议：`aiApiKey.encryptKey`（32 字节），环境/密管注入，不入库、不进仓库。
- 每条记录独立随机 nonce。

---

## 4. 51PM 接口

### 4.1 对外（`/manage_api/ai_api_key/*`，走现有 Auth）

| Method | Path | 说明 |
|---|---|---|
| POST | `/manage_api/ai_api_key/create_ai_api_key` | body: `provider_name, base_url, api_key, default_model?` |
| PUT | `/manage_api/ai_api_key/update_ai_api_key` | body: `id, provider_name?, base_url?, api_key?, default_model?` |
| POST | `/manage_api/ai_api_key/delete_ai_api_key` | body: `{ id }` |
| GET | `/manage_api/ai_api_key/get_ai_api_key_list` | 当前用户列表（掩码） |
| POST | `/manage_api/ai_api_key/set_default_ai_api_key` | body: `{ id }` |
| POST | `/manage_api/ai_api_key/refresh_ai_api_key_models` | body: `{ id }` |
| POST | `/manage_api/ai_api_key/reveal_ai_api_key_secret` | 一次性明文；写审计日志；登录态即可 |
| GET | `/manage_api/ai_api_key/get_ai_api_key_status` | `{ configured: bool, default_model }` |

隔离：一律 `g.RequestFromCtx(ctx).GetCtxVar("uid")`。

### 4.2 内部（不对前端暴露）

- **POST** `/internal_api/ai_api_key/resolve`
- Header：`X-Internal-Secret`
- Body：`{ "oauth_token": "<token>" }`
- 用 Redis `user_info:{token}` 解析用户 → 取 `is_default=1` → 解密
- 响应：
  - 200：`{ code: 0, data: { base_url, api_key, model } }`
  - 401：`invalid_token`
  - 404：`not_configured`
- 路由独立于 `/manage_api`；校验 Internal Secret（建议后续可叠加 IP 白名单）

配置项建议：

```yaml
aiApiKey:
  encryptKey: "<32-byte-secret>"
  internalSecret: "<shared-with-agent>"
```

---

## 5. AI-Skill-Platform 改造

### 5.1 新增配置

| 环境变量 | 说明 |
|---|---|
| `BIZ_BASE_URL` | 51PM 根地址 |
| `BIZ_INTERNAL_SECRET` | 与 51PM `aiApiKey.internalSecret` 一致 |
| `BIZ_RESOLVE_TIMEOUT_SECONDS` | resolve 超时，默认如 5 |

既有 `LLM_*` 仅用于 FakeLLMClient / 单测注入构造；**正式** `/v1/execute`、`/v1/chat` 路径禁止使用其作为用户请求兜底。

### 5.2 请求处理流程

1. 读取 `Authorization: Bearer <token>`；缺失 → `status=unauthorized`
2. `POST {BIZ_BASE_URL}/internal_api/ai_api_key/resolve`
3. 映射：
   - 业务 401 → `unauthorized`
   - 业务 404 → `no_api_key`
   - 超时/5xx → `llm_error`（不 fallback）
4. 用 `base_url/api_key/model` 构造本次 `HttpLLMClient`（支持覆盖构造参数）
5. 经 Runtime / Skill 执行链透传该 client；`qa_board_analysis`、`qa_notes_ai_fill`（及后续 LLM skill）不得再 `HttpLLMClient(get_settings())`

### 5.3 状态约定（`AgentResponse.status`）

| status | 含义 |
|---|---|
| `ok` | 成功 |
| `unauthorized` | 无/无效登录态 |
| `no_api_key` | 已登录但未配置生效 Key |
| `llm_error` | resolve 或上游 LLM 失败 |
| （既有）`need_slot` / `unknown_intent` 等 | 保持不变 |

---

## 6. 前端交付物（仅文档）

路径建议：`E:\51PM\docs\superpowers\api\2026-08-10-user-ai-api-key-frontend.md`

内容须覆盖：

1. 配置类接口：path、鉴权、请求/响应示例、错误码
2. 消费侧联调：
   - `executeSkill` 必须带 `Authorization: Bearer <oauthToken>`
   - 可选预检 `get_ai_api_key_status`
   - 处理 `no_api_key` / `unauthorized`（引导去配置页，路径约定 `/ai_api_key_config`）
   - Internal Secret / resolve **仅服务端**，前端不感知

---

## 7. 测试要点

**51PM**

- 加密往返正确；掩码接口无明文
- 用户隔离；首条自动 default；删生效自动切最新
- resolve：错 Secret → 拒绝；坏 token → 401；未配置 → 404；成功返回三元组

**AI-Skill-Platform**

- 无 Bearer → `unauthorized`
- resolve 404 → `no_api_key`
- 成功路径 skill 使用用户 model（可用 Fake resolve + Fake LLM）
- 断言 session/logs 不含 api_key

**联调**

- 51PM 写入一条真实/兼容 Key → Agent `/v1/execute` 跑通至少一种 LLM skill

---

## 8. 已拍板的产品决策

| 问题 | 决策 |
|---|---|
| 实现范围 | 后端双端 + 前端仅文档 |
| 调用拓扑 | 方案 A（Agent → 51PM resolve） |
| 全局 Key 回退 | 严格禁止（含本地） |
| 复制明文 | 登录态即可；记审计日志 |
| 共享 Key | 不做 |
| 模型列表探测失败 | 允许手填模型名 |
| 生效粒度 | 全局一条覆盖所有 AI 功能 |
| 删除生效 Key | 自动将剩余最新一条设为默认 |

---

## 9. 实现顺序建议

1. 51PM：加密工具 + 表/DAO + CRUD + resolve  
2. AI-Skill-Platform：resolve 客户端 + per-request LLM + execute/chat 接入  
3. 联调 + 前端 API/联调文档  
4. （后续另开）前端页面与 `executeSkill` 改造
