# User AI API Key Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用户在 51PM 加密保存个人 LLM API Key；AI-Skill-Platform 按请求 Bearer 向 51PM resolve 后使用该用户凭据调用模型，严格无全局 Key 回退；前端仅交付接口/联调文档。

**Architecture:** 方案 A——浏览器带 `Authorization` 直连 Agent → Agent 用 `X-Internal-Secret` 调 51PM `/internal_api/ai_api_key/resolve` → 用返回的 `base_url/api_key/model` 构造本次 `HttpLLMClient`。密钥 AES-256-GCM 落库；明文仅瞬时存在于 reveal/resolve。

**Tech Stack:** 51PM GoFrame v2 + MySQL + Redis；AI-Skill-Platform FastAPI + httpx + pydantic-settings；pytest / Go `testing`。

**Spec:** `docs/superpowers/specs/2026-08-10-user-ai-api-key-design.md`（两仓各有一份）

## Global Constraints

- 正式 `/v1/execute`、`/v1/chat` **禁止** fallback 到 `.env` 的 `LLM_*`
- 日志与 `SessionStore` **禁止**出现 api_key 明文
- 表名按 51PM 惯例使用 `dev_user_ai_api_key`（相对草案 `user_ai_api_key` 的命名对齐）
- `user_id` 一律从登录态 / Redis token 解析，禁止请求体传入
- 删除当前生效 Key 且仍有剩余时：自动将剩余 `id` 最大的一条设为 `is_default=1`
- 模型列表 `GET {base_url}/models` 失败时允许手填 `default_model`；服务商 HTTP 401 则创建/更新不落库
- 提交代码前勿把真实 `encryptKey` / `internalSecret` / 用户 Key 写入仓库

## File Structure

### 51PM（`E:\51PM`）

| Path | Responsibility |
|---|---|
| `docs/sql/dev_user_ai_api_key.sql` | 建表 DDL |
| `utility/aiapikey/crypto.go` | AES-256-GCM Encrypt/Decrypt + Mask |
| `utility/aiapikey/crypto_test.go` | 加解密单测 |
| `utility/aiapikey/provider.go` | 调服务商 `/models` 探测 |
| `internal/model/entity/dev_user_ai_api_key.go` | 实体 |
| `internal/model/do/dev_user_ai_api_key.go` | DO |
| `internal/dao/internal/dev_user_ai_api_key.go` | 内部 DAO |
| `internal/dao/dev_user_ai_api_key.go` | 对外 DAO |
| `api/manage_api/ai_api_key/ai_api_key.go` | 对外 API 定义 |
| `api/internal_api/ai_api_key/ai_api_key.go` | 内部 resolve API 定义 |
| `internal/model/ai_api_key.go` | 列表项等 DTO |
| `internal/service/ai_api_key.go` | IAiApiKey 接口 |
| `internal/logic/ai_api_key/ai_api_key.go` | 业务实现 |
| `internal/controller/ai_api_key/ai_api_key.go` | 对外 controller |
| `internal/controller/internal_api/ai_api_key.go` | resolve controller |
| `internal/cmd/router.go` | 注册 `/manage_api/ai_api_key` 与 `/internal_api` |
| `manifest/config/config.example.yaml` | `aiApiKey.encryptKey` / `internalSecret` |
| `docs/superpowers/api/2026-08-10-user-ai-api-key-frontend.md` | 前端接口+联调文档 |

### AI-Skill-Platform（`E:\AI-Skill-Platform`）

| Path | Responsibility |
|---|---|
| `app/config.py` | `biz_base_url` / `biz_internal_secret` / resolve timeout |
| `.env.example` | 同步新变量说明 |
| `app/llm/credentials.py` | ContextVar + `get_request_llm_client()` |
| `app/llm/client.py` | 支持显式 `base_url/api_key/model` 构造 |
| `app/biz/resolve.py` | 调 51PM resolve |
| `app/api/v1/execute.py` / `chat.py` | 取 Bearer → resolve → set credentials |
| `app/conversation/controller.py` | chat 路径同样先 resolve |
| `app/skills/qa_board_analysis/executor.py` | 改用 `get_request_llm_client()` |
| `app/skills/qa_notes_ai_fill/executor.py` | 同上 |
| `tests/test_biz_resolve.py` / `test_llm_credentials.py` / `test_execute_auth.py` | 单测 |

---

### Task 1: 51PM — 建表 DDL + AES 工具

**Files:**
- Create: `E:/51PM/docs/sql/dev_user_ai_api_key.sql`
- Create: `E:/51PM/utility/aiapikey/crypto.go`
- Create: `E:/51PM/utility/aiapikey/crypto_test.go`

**Interfaces:**
- Produces: `Encrypt(plain, key []byte) (string, error)`、`Decrypt(blob string, key []byte) (string, error)`、`Mask(plain string) string`；密文格式 `base64(nonce||ciphertext||tag)`

- [ ] **Step 1: Write failing crypto test**

```go
package aiapikey

import (
	"bytes"
	"testing"
)

func TestEncryptDecryptRoundTrip(t *testing.T) {
	key := bytes.Repeat([]byte("k"), 32)
	plain := "sk-test-secret-key"
	enc, err := Encrypt(plain, key)
	if err != nil {
		t.Fatal(err)
	}
	if enc == plain {
		t.Fatal("ciphertext must differ from plaintext")
	}
	got, err := Decrypt(enc, key)
	if err != nil {
		t.Fatal(err)
	}
	if got != plain {
		t.Fatalf("got %q", got)
	}
}

func TestMask(t *testing.T) {
	if Mask("sk-abcdefghijklmnop") != "sk-abcd****mnop" && len(Mask("sk-abcdefghijklmnop")) < 8 {
		t.Fatalf("unexpected mask: %s", Mask("sk-abcdefghijklmnop"))
	}
}
```

Mask 规则实现为：长度 ≥ 12 时保留前 6 + `****` + 后 4；否则返回 `****`。

- [ ] **Step 2: Run test — expect fail**

```bash
cd E:/51PM && go test ./utility/aiapikey/ -v
```

Expected: FAIL（package/functions undefined）

- [ ] **Step 3: Implement crypto + SQL**

`utility/aiapikey/crypto.go`：标准库 `crypto/aes` + `cipher.NewGCM`；Encrypt 随机 12 字节 nonce；Decrypt 校验长度。

`docs/sql/dev_user_ai_api_key.sql`：

```sql
CREATE TABLE IF NOT EXISTS `dev_user_ai_api_key` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL COMMENT 'dev_yunwei_user.id',
  `provider_name` VARCHAR(128) NOT NULL DEFAULT '',
  `base_url` VARCHAR(512) NOT NULL DEFAULT '',
  `api_key_encrypted` TEXT NOT NULL,
  `api_key_mask` VARCHAR(64) NOT NULL DEFAULT '',
  `available_models` JSON NULL,
  `default_model` VARCHAR(128) NOT NULL DEFAULT '',
  `is_default` TINYINT NOT NULL DEFAULT 0,
  `status` VARCHAR(32) NOT NULL DEFAULT 'ok',
  `last_verified_at` DATETIME NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_user_default` (`user_id`, `is_default`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户个人 AI API Key';
```

- [ ] **Step 4: Run tests — expect pass**

```bash
cd E:/51PM && go test ./utility/aiapikey/ -v
```

- [ ] **Step 5: Commit（仅当用户明确要求提交时执行）**

```bash
cd E:/51PM
git add docs/sql/dev_user_ai_api_key.sql utility/aiapikey/
git commit -m "$(cat <<'EOF'
feat: add AI API key table DDL and AES-GCM helpers

EOF
)"
```

---

### Task 2: 51PM — DAO/Entity + 配置项

**Files:**
- Create: entity/do/dao（手写对齐 `dev_user_custom_group` 风格，或 `gf gen dao` 后提交）
- Modify: `E:/51PM/manifest/config/config.example.yaml` — 追加：

```yaml
aiApiKey:
  encryptKey: ""       # 32 字节主密钥，勿提交真实值
  internalSecret: ""   # Agent 服务间 X-Internal-Secret
  verifyTimeout: 15    # 探测 /models 超时秒数
```

**Interfaces:**
- Produces: `dao.DevUserAiApiKey` 可 CRUD

- [ ] **Step 1: 生成或手写 DAO 层文件**（字段与 DDL 一致；JSON 字段用 `string` 或 `*string` 存序列化后的 models）

- [ ] **Step 2: 本地执行 DDL**（开发库）

```bash
# 使用现有 MySQL 客户端执行 docs/sql/dev_user_ai_api_key.sql
```

- [ ] **Step 3: Commit（用户要求时）**

---

### Task 3: 51PM — 对外 CRUD API

**Files:**
- Create: `api/manage_api/ai_api_key/ai_api_key.go`
- Create: `internal/model/ai_api_key.go`（`AiApiKeyListItem` 等，无明文）
- Create: `internal/service/ai_api_key.go`
- Create: `internal/logic/ai_api_key/ai_api_key.go`（含 `init` Register）
- Create: `internal/controller/ai_api_key/ai_api_key.go`
- Create: `utility/aiapikey/provider.go`（`ListModels(ctx, baseURL, apiKey) ([]string, error)`）
- Modify: `internal/cmd/router.go` — Auth 后：

```go
group.Group("/ai_api_key", func(g2 *ghttp.RouterGroup) {
    g2.Bind(aiapikeyctrl.AiApiKey)
})
```

**Interfaces:**
- Consumes: `aiapikey.Encrypt/Decrypt/Mask`、`dao.DevUserAiApiKey`、ctx `uid`
- Produces: 下列 HTTP 接口（路径前缀 `/manage_api/ai_api_key`）

| Method | Path |
|---|---|
| POST | `/create_ai_api_key` |
| PUT | `/update_ai_api_key` |
| POST | `/delete_ai_api_key` |
| GET | `/get_ai_api_key_list` |
| POST | `/set_default_ai_api_key` |
| POST | `/refresh_ai_api_key_models` |
| POST | `/reveal_ai_api_key_secret` |
| GET | `/get_ai_api_key_status` |

- [ ] **Step 1: 实现 `provider.ListModels`**

`GET {baseURL}/models`，Header `Authorization: Bearer {apiKey}`；解析 OpenAI 风格 `data[].id`；网络错误返回 error；HTTP 401 返回可识别错误（logic 据此不落库）。

- [ ] **Step 2: 实现 Create 逻辑要点**

```go
uid := g.RequestFromCtx(ctx).GetCtxVar("uid").Int()
// 1) ListModels；若 401 → 返回错误
// 2) 非 401 的探测失败：available_models=[]，仍要求 default_model 非空（手填）
// 3) Encrypt(apiKey, encryptKey)
// 4) 若该用户无任何记录 → is_default=1
// 5) Insert；列表返回不包含明文
```

- [ ] **Step 3: 实现 Update / Delete / SetDefault / Refresh / Reveal / Status / List**

Delete 伪代码：

```go
// 删除前记录 wasDefault
// Delete where id AND user_id=uid
// if wasDefault {
//   next := 同用户剩余按 id DESC 第一条
//   if next != nil { set is_default=1 }
// }
```

Reveal：Decrypt 后返回 `{ api_key: plain }`；`g.Log().Infof` 审计（只打 user_id、record id，**不打明文**）。

Status：`configured = 存在 is_default=1 且 default_model 非空（或允许 model 空？——规格要求有生效 Key；若 default_model 空，Agent 调用会失败，status 仍算 configured=true 但建议 Create 强制 default_model）`。**强制：create/update 必须最终有非空 `default_model`。**

- [ ] **Step 4: 手工或写 Go 测试验证列表无明文、跨用户拒绝**

- [ ] **Step 5: Commit（用户要求时）**

---

### Task 4: 51PM — 内部 resolve

**Files:**
- Create: `api/internal_api/ai_api_key/ai_api_key.go`
- Create: `internal/controller/internal_api/ai_api_key.go`
- Modify: `internal/logic/ai_api_key/ai_api_key.go` — 增加 `Resolve(ctx, oauthToken string)`
- Modify: `internal/cmd/router.go`：

```go
s.Group("/internal_api", func(group *ghttp.RouterGroup) {
    group.Middleware(middleware.RequestLog, middleware.HandlerResponse, middleware.MiddlewareCORS)
    // 无 Auth；在 handler 内校验 X-Internal-Secret
    group.Group("/ai_api_key", func(g2 *ghttp.RouterGroup) {
        g2.Bind(internalaiapikey.AiApiKey.Resolve)
    })
})
```

**Interfaces:**
- Produces: `POST /internal_api/ai_api_key/resolve`  
  Body: `{ "oauth_token": "..." }`  
  Success data: `{ "base_url", "api_key", "model" }`  
  Fail: `code=401` invalid_token；`code=404` not_configured；错 Secret → HTTP 403 或 `code=403`

- [ ] **Step 1: Resolve 实现**

```go
func (s *sAiApiKey) Resolve(ctx context.Context, oauthToken string) (baseURL, apiKey, model string, code int, err error) {
    secret := r.Header.Get("X-Internal-Secret") // 在 controller 校验
    // Redis: consts.USER_INFO_KEY + oauthToken → UserInfo.UserId
    // 查 is_default=1 AND user_id=?
    // Decrypt → return
}
```

错 Secret：直接 `response.JsonExit(r, 403, "forbidden")`。  
Token 无效：`code=401`。无默认 Key：`code=404, msg=not_configured`。

- [ ] **Step 2: 用 curl 验证三种响应（需本地 Redis 有测试 token）**

- [ ] **Step 3: Commit（用户要求时）**

---

### Task 5: Skill Platform — resolve 客户端 + ContextVar

**Files:**
- Modify: `app/config.py`、`.env.example`
- Create: `app/biz/__init__.py`、`app/biz/resolve.py`
- Create: `app/llm/credentials.py`
- Modify: `app/llm/client.py`
- Test: `tests/test_biz_resolve.py`、`tests/test_llm_credentials.py`

**Interfaces:**
- Produces:
  - `Settings.biz_base_url: str`、`biz_internal_secret: str`、`biz_resolve_timeout_seconds: float = 5`
  - `class ResolvedLLM: base_url: str; api_key: str; model: str`
  - `resolve_user_llm(token: str, settings: Settings) -> ResolvedLLM`  
    raises `AppError(code="unauthorized"|"no_api_key"|"llm_error", ...)`
  - `set_request_llm(resolved: ResolvedLLM) -> Token` / `reset_request_llm(token)`
  - `get_request_llm_client() -> LLMClient` — 无上下文则 `AppError(code="unauthorized", ...)`
  - `HttpLLMClient(settings=None, *, base_url=..., api_key=..., model=..., timeout=...)`

- [ ] **Step 1: 写失败测试**

```python
def test_resolve_maps_404_to_no_api_key(httpx_mock):
    # mock POST .../internal_api/ai_api_key/resolve → 200 body {"code":404,"msg":"not_configured"}
    # or HTTP 404
    with pytest.raises(AppError) as ei:
        resolve_user_llm("tok", settings)
    assert ei.value.code == "no_api_key"

def test_get_request_llm_client_requires_context():
    with pytest.raises(AppError) as ei:
        get_request_llm_client()
    assert ei.value.code == "unauthorized"
```

- [ ] **Step 2: 实现 resolve + credentials + HttpLLMClient 覆盖构造**

`resolve.py` 解析约定：HTTP 200 且 `body.code==0` 为成功；`code==401`→unauthorized；`code==404`→no_api_key；其它/网络→llm_error。响应 `data` 取三字段。请求头带 `X-Internal-Secret`，body `{"oauth_token": token}`。

`HttpLLMClient.__init__`：若传入 `base_url/api_key/model` 则用之，否则读 `settings`（**仅 Fake/单测**直接构造 Settings 客户端时使用；生产路径只走 Resolved）。

`get_request_llm_client()`：

```python
def get_request_llm_client() -> LLMClient:
    creds = _llm_ctx.get()
    if creds is None:
        raise AppError(code="unauthorized", message="Missing LLM credentials", status_code=401)
    return HttpLLMClient(
        settings=get_settings(),
        base_url=creds.base_url,
        api_key=creds.api_key,
        model=creds.model,
    )
```

- [ ] **Step 3: pytest 通过**

```bash
cd E:/AI-Skill-Platform && .\.venv\Scripts\python.exe -m pytest tests/test_biz_resolve.py tests/test_llm_credentials.py -q
```

- [ ] **Step 4: Commit（用户要求时）**

---

### Task 6: Skill Platform — execute/chat 接入 + skill 改造

**Files:**
- Modify: `app/api/v1/execute.py`、`app/api/v1/chat.py`
- Modify: `app/conversation/controller.py`（若 chat 在 controller 内调 LLM，先 resolve）
- Modify: `app/skills/qa_board_analysis/executor.py`
- Modify: `app/skills/qa_notes_ai_fill/executor.py`
- Modify: 其它直接 `HttpLLMClient(get_settings())` 的 skill（全库 grep）
- Test: `tests/test_execute_auth.py`；更新既有 `test_qa_board_analysis.py` / `test_qa_notes_ai_fill.py`：在调用前 `set_request_llm` 或 mock resolve

**Interfaces:**
- Consumes: `resolve_user_llm`、`set_request_llm`
- Produces: `/v1/execute`、`/v1/chat` 在成功路径设置凭据；失败返回 `AgentResponse.status` ∈ `{unauthorized, no_api_key, llm_error}`

- [ ] **Step 1: 写 execute 鉴权测试**

```python
def test_execute_without_authorization_returns_unauthorized():
    r = client.post("/v1/execute", json={"intent": "echo", "slots": {"text": "hi"}})
    assert r.json()["status"] == "unauthorized"

def test_execute_no_api_key(monkeypatch):
    def boom(token, settings):
        raise AppError(code="no_api_key", message="not_configured", status_code=404)
    monkeypatch.setattr("app.biz.resolve.resolve_user_llm", boom)
    r = client.post(
        "/v1/execute",
        headers={"Authorization": "Bearer t"},
        json={"intent": "echo", "slots": {"text": "hi"}},
    )
    assert r.json()["status"] == "no_api_key"
```

注意：`echo` 不调 LLM——**即便如此也必须先 resolve**（规格：正式请求一律用用户 Key；无 Key 则阻断所有 execute，含非 LLM skill）。这样前端统一预检逻辑更简单。

- [ ] **Step 2: execute.py 改造**

```python
@router.post("/v1/execute", response_model=AgentResponse)
def execute(body: ExecuteRequest, request: Request, runtime: RuntimeService = Depends(get_runtime)):
    auth = request.headers.get("Authorization") or ""
    if not auth.lower().startswith("bearer "):
        return AgentResponse(session_id=..., status="unauthorized", ...)  # 或生成临时 session
    token = auth.split(" ", 1)[1].strip()
    try:
        resolved = resolve_user_llm(token, get_settings())
    except AppError as exc:
        if exc.code in ("unauthorized", "no_api_key", "llm_error"):
            session = runtime.sessions.create(body.session_id)
            return AgentResponse(session_id=session.session_id, status=exc.code, reply=exc.message)
        raise
    ctx_token = set_request_llm(resolved)
    try:
        result = runtime.run(body.intent, body.slots, body.session_id)
        return AgentResponse(**result.__dict__)
    finally:
        reset_request_llm(ctx_token)
```

`chat` 同样处理（在进 `handle_chat` 前 resolve；意图路由 LLM 与 skill LLM 共用 ContextVar）。

- [ ] **Step 3: skill executor 替换**

```python
# was: client = HttpLLMClient(get_settings())
from app.llm.credentials import get_request_llm_client
client = get_request_llm_client()
```

- [ ] **Step 4: 更新旧测试：在 TestClient 调用前 set_request_llm 假凭据，或 mock resolve 返回固定值**

- [ ] **Step 5: 全量 pytest**

```bash
cd E:/AI-Skill-Platform && .\.venv\Scripts\python.exe -m pytest -q
```

Expected: all pass

- [ ] **Step 6: Commit（用户要求时）**

---

### Task 7: 前端接口与联调文档

**Files:**
- Create: `E:/51PM/docs/superpowers/api/2026-08-10-user-ai-api-key-frontend.md`

**内容必须包含：**

1. 配置类 8 个接口的 method/path/body/响应示例（掩码、无明文）
2. `get_ai_api_key_status` 预检约定
3. Agent 消费：`POST {VUE_APP_AGENT_API}/v1/execute` 必须 `Authorization: Bearer ${oauthToken}`
4. `status === 'no_api_key' | 'unauthorized'` 处理：弹窗 + 跳转 `/ai_api_key_config`
5. 声明 Internal Secret / resolve 仅服务端
6. 联调检查清单（51PM 配 Key → Agent 带 token 调 skill）

- [ ] **Step 1: 按现有 `docs/superpowers/api/2026-08-07-project-moment-stat-frontend.md` 文风撰写完整文档**

- [ ] **Step 2: Commit（用户要求时）**

---

### Task 8: 联调验收（手工）

- [ ] **Step 1:** 两边配置 `aiApiKey.encryptKey`（32 字节）与相同 `internalSecret`；Agent `.env` 设 `BIZ_BASE_URL`、`BIZ_INTERNAL_SECRET`
- [ ] **Step 2:** 用真实登录 token 调 `create_ai_api_key` 写入一条可用 Key
- [ ] **Step 3:** `POST /v1/execute` 带 Bearer，intent `qa_board_analysis` 或 `echo`（echo 验证 resolve 门禁；LLM skill 验证真调用）
- [ ] **Step 4:** 无 Bearer / 删光 Key 分别验证 `unauthorized` / `no_api_key`
- [ ] **Step 5:** 确认 Agent 与 51PM 日志无 api_key 明文

---

## Spec coverage checklist

| Spec 项 | Task |
|---|---|
| 表 + AES-GCM | 1–2 |
| 对外 CRUD / reveal / status | 3 |
| 内部 resolve | 4 |
| Agent resolve + 无回退 | 5–6 |
| skill 不用 get_settings Key | 6 |
| 前端仅文档 | 7 |
| 联调 | 8 |
| 删生效自动切最新 | 3 |
| 手填模型 | 3 |
| 审计 reveal | 3 |

## Execution Handoff

Plan complete and saved to:

- `E:\51PM\docs\superpowers\plans\2026-08-10-user-ai-api-key.md`
- `E:\AI-Skill-Platform\docs\superpowers\plans\2026-08-10-user-ai-api-key.md`（镜像）

**Two execution options:**

1. **Subagent-Driven（推荐）** — 每任务新开子代理，任务间复审  
2. **Inline Execution** — 本会话按 executing-plans 连续推进并设检查点  

Which approach?
