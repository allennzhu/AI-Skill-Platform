from __future__ import annotations

import json
import re
from typing import Any

from app.api.errors import AppError
from app.llm.credentials import get_request_llm_client

_THINK_RE = re.compile(r"<think>[\s\S]*?</think>", re.IGNORECASE)
_THINK_UNCLOSED_RE = re.compile(r"<think>[\s\S]*$", re.IGNORECASE)

SYSTEM_PROMPT = """你是 51PM 项目进展分析助手。
你会收到一段 JSON，包含某项目在给定时间段内的：制作需求申请与拆解、客户反馈、递交排期执行、成员日报花费等汇总数据。
请基于这些数据写一段完整的中文分析总结，帮助 PM/TB/管理层快速把握项目状态。

硬性要求：
1. 只输出完整的一段话（可包含 4～10 句，必须连贯成段）。
2. 不要使用项目符号、编号列表、小标题或 Markdown。
3. 不要输出 JSON 或代码块。
4. 只能使用给定数据中的信息与合理归纳，禁止编造未出现的数字、人名或事实。
5. 重点覆盖：整体推进态势、制作需求与反馈风险、递交是否按时、日报反映的主要工作与阻塞、需要优先跟进的事项。
6. 若某块数据为空或 total 为 0，可简要说明「该维度暂无记录」，不要展开臆测。
"""


def _clean_reply(text: str) -> str:
    cleaned = _THINK_RE.sub("", text or "")
    cleaned = _THINK_UNCLOSED_RE.sub("", cleaned)
    cleaned = cleaned.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:\w+)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def execute(slots: dict[str, Any]) -> dict[str, Any]:
    context = slots.get("context") or {}
    payload = json.dumps(context, ensure_ascii=False, default=str)
    user_prompt = (
        "请根据以下项目进展统计 JSON，写一段完整的中文分析总结：\n\n"
        f"{payload}"
    )
    client = get_request_llm_client()
    try:
        raw = client.complete(SYSTEM_PROMPT, user_prompt)
    except AppError:
        raise
    reply = _clean_reply(raw)
    if not reply:
        raise AppError(code="llm_error", message="LLM 未返回项目进展分析", status_code=502)
    return {"reply": reply, "context_keys": sorted(context.keys())}
