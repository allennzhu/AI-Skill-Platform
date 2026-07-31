import json
import re
from typing import Any

from app.api.errors import AppError


_JSON_FENCE = re.compile(r"^\s*```(?:json)?\s*\n?(.*?)\n?\s*```\s*$", re.DOTALL | re.IGNORECASE)


def parse_intent_json(text: str) -> dict[str, Any]:
    match = _JSON_FENCE.match(text)
    payload = match.group(1).strip() if match else text.strip()

    try:
        parsed = json.loads(payload)
    except (json.JSONDecodeError, TypeError) as exc:
        raise AppError(
            code="llm_error",
            message="LLM returned invalid JSON",
            status_code=502,
        ) from exc

    if not isinstance(parsed, dict) or "intent" not in parsed:
        raise AppError(
            code="llm_error",
            message="LLM response is missing intent",
            status_code=502,
        )

    slots = parsed.get("slots", {})
    if not isinstance(parsed["intent"], str) or not isinstance(slots, dict):
        raise AppError(
            code="llm_error",
            message="LLM response has invalid intent or slots",
            status_code=502,
        )

    return {"intent": parsed["intent"], "slots": slots}
