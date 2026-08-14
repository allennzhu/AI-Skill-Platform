from typing import Any


def build_response(result: dict[str, Any]) -> dict[str, Any]:
    reply = (result or {}).get("reply") or ""
    return {
        "result": {
            "summary": reply,
            "scope": (result or {}).get("scope"),
            "period": (result or {}).get("period"),
            "context_keys": (result or {}).get("context_keys") or [],
        },
        "reply": reply,
    }
