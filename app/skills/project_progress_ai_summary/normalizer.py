from __future__ import annotations

import json
from typing import Any

_MAX_CHARS = 12000


def _trim_value(value: Any, depth: int = 0) -> Any:
    if depth > 6:
        return "..."
    if isinstance(value, dict):
        return {str(k): _trim_value(v, depth + 1) for k, v in list(value.items())[:80]}
    if isinstance(value, list):
        return [_trim_value(v, depth + 1) for v in value[:40]]
    if isinstance(value, str) and len(value) > 500:
        return value[:500] + "…"
    return value


def normalize(slots: dict[str, Any]) -> dict[str, Any]:
    context = _trim_value(slots.get("context") or {})
    raw = json.dumps(context, ensure_ascii=False, default=str)
    if len(raw) <= _MAX_CHARS:
        return {"context": context}

    compact = {
        "project": context.get("project"),
        "period": context.get("period"),
        "produce_demand": context.get("produce_demand"),
        "publish": context.get("publish"),
        "daily": context.get("daily"),
        "_truncated": True,
        "_original_chars": len(raw),
    }
    compact_raw = json.dumps(compact, ensure_ascii=False, default=str)
    if len(compact_raw) > _MAX_CHARS:
        compact = {
            "project": context.get("project"),
            "period": context.get("period"),
            "data_excerpt": compact_raw[:_MAX_CHARS],
            "_truncated": True,
        }
    return {"context": compact}
