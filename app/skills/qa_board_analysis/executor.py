from __future__ import annotations

import json
import re
from typing import Any

from app.api.errors import AppError
from app.llm.credentials import get_request_llm_client

_THINK_RE = re.compile(r"<think>[\s\S]*?</think>", re.IGNORECASE)
_THINK_UNCLOSED_RE = re.compile(r"<think>[\s\S]*$", re.IGNORECASE)

SYSTEM_PROMPT = """你是测试数据看板的质量分析助手。
你会收到一段 JSON，内容来自看板接口：周期与筛选、KPI、BUG 维度、递交维度、QA 总结。
请基于这些数据写一段完整的中文分析结论。

硬性要求：
1. 只输出完整的一段话（可包含 3～8 句，必须连贯成段）。
2. 不要使用项目符号、编号列表、小标题或 Markdown。
3. 不要输出 JSON 或代码块。
4. 只能使用给定数据中的信息与合理归纳，禁止编造未出现的数字或事实。
5. 重点覆盖：整体质量态势、主要风险或异常、值得关注的部门/项目/递交情况、结合总结区（若有）的建议方向。
"""


def _clean_reply(text: str) -> str:
    cleaned = _THINK_RE.sub("", text or "")
    cleaned = _THINK_UNCLOSED_RE.sub("", cleaned)
    cleaned = cleaned.strip()
    # Drop accidental fences
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:\w+)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def execute(slots: dict[str, Any]) -> dict[str, Any]:
    context = slots.get("context") or {}
    payload = json.dumps(context, ensure_ascii=False, default=str)
    user_prompt = (
        "请根据以下测试数据看板统计 JSON，写一段完整的中文分析结论：\n\n"
        f"{payload}"
    )
    client = get_request_llm_client()
    try:
        raw = client.complete(SYSTEM_PROMPT, user_prompt)
    except AppError:
        raise
    reply = _clean_reply(raw)
    if not reply:
        raise AppError(code="llm_error", message="LLM returned empty analysis", status_code=502)
    return {"reply": reply, "context_keys": sorted(context.keys())}
