from typing import Any

_EMPTY_NOTES: dict[str, Any] = {
    "role_reviews": [],
    "bug_summary": "",
    "bug_suggestions": {"art": "", "program": "", "qa": ""},
    "focus_items": [],
    "process_items": [],
}


def build_response(result: dict[str, Any]) -> dict[str, Any]:
    result = result or {}
    notes = result.get("notes") or dict(_EMPTY_NOTES)
    return {
        "result": {
            "notes": notes,
            "sections": result.get("sections") or [],
            "period": result.get("period"),
            "context_keys": result.get("context_keys") or [],
        },
        # reply 供对话式调用兜底展示；前端回填走 result.notes
        "reply": notes.get("bug_summary") or "AI 分析完成，请查看回填内容。",
    }
