from typing import Any

_EMPTY_MOMENT: dict[str, Any] = {
    "type": "",
    "content": "",
    "attendees": [],
    "todos": [],
}


def build_response(result: dict[str, Any]) -> dict[str, Any]:
    result = result or {}
    moment = result.get("moment") or dict(_EMPTY_MOMENT)
    return {
        "result": {
            "moment": moment,
        },
        # reply 供对话式调用兜底展示；前端回填走 result.moment
        "reply": moment.get("content") or "AI 已完成会议纪要抽取，请查看回填内容。",
    }
