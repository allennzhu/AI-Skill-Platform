from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.api.errors import AppError
from app.llm.credentials import get_request_llm_client

_THINK_RE = re.compile(r"<think>[\s\S]*?</think>", re.IGNORECASE)
_THINK_UNCLOSED_RE = re.compile(r"<think>[\s\S]*$", re.IGNORECASE)
_PROMPT_PATH = Path(__file__).with_name("prompt.md")
SYSTEM_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")


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
    user_note = (slots.get("user_note") or "").strip()
    scope = slots.get("scope") or "personal"
    extra = f"\n\n用户补充说明：{user_note}" if user_note else ""
    user_prompt = (
        f"本次为「{'部门' if scope == 'department' else '个人'}」工作总结（scope={scope}）。\n"
        "请根据以下工时 JSON 生成工作总结：\n\n"
        f"{payload}{extra}"
    )
    client = get_request_llm_client()
    try:
        raw = client.complete(SYSTEM_PROMPT, user_prompt)
    except AppError:
        raise
    reply = _clean_reply(raw)
    if not reply:
        raise AppError(code="llm_error", message="LLM 未返回工作总结", status_code=502)
    return {
        "reply": reply,
        "scope": scope,
        "period": context.get("period"),
        "context_keys": sorted(k for k in context.keys() if not str(k).startswith("_")),
    }
