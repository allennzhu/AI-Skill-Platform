# AI Skill Platform

FastAPI agent shell with LLM-driven chat and direct skill execution.
对外由 **51PM** 代理 `/manage_api/ai_skill/execute`、`/manage_api/ai_skill/chat`；本服务仅内网监听，浏览器不要直连。

模型凭据来自用户在 51PM 配置的个人 API Key（按请求 resolve），进程内无全局 `LLM_BASE_URL` / `LLM_API_KEY`。

## Requirements

- Python 3.11+
- 已启动的 51PM（`BIZ_BASE_URL` + `BIZ_INTERNAL_SECRET` 与 51PM `aiApiKey.internalSecret` 一致）

## Install

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
# Windows
copy .env.example .env
# Linux / macOS
cp .env.example .env
```

## Start

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

`HOST` / `PORT` 仅作文档默认值；uvicorn 不会自动读 `.env` 里的这两项。`LLM_TIMEOUT_SECONDS`（默认 `120`）等从 `.env` 加载。51PM `aiSkill.baseUrl` 需指向本进程实际地址。

## API examples

内网直连本服务时必须带用户 `Authorization: Bearer <oauthToken>`。前端应打 51PM 代理，而不是下列地址。

### Health

```bash
curl -s http://127.0.0.1:8000/health
```

Expected: `{"status":"ok"}`

### Execute — echo

```bash
curl -s -X POST http://127.0.0.1:8000/v1/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <oauthToken>" \
  -d "{\"intent\":\"echo\",\"slots\":{\"text\":\"hi\"}}"
```

### Execute — health skill

```bash
curl -s -X POST http://127.0.0.1:8000/v1/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <oauthToken>" \
  -d "{\"intent\":\"health\",\"slots\":{}}"
```
