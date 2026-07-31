import json
import re
from typing import Any

from app.api.errors import AppError


_JSON_FENCE = re.compile(r"^\s*```(?:json)?\s*\n?(.*?)\n?\s*```\s*$", re.DOTALL | re.IGNORECASE)
_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_UNCLOSED_THINK = re.compile(r"<think>", re.IGNORECASE)


def _strip_think_blocks(text: str) -> str:
    payload = _THINK_BLOCK.sub("", text)
    match = _UNCLOSED_THINK.search(payload)
    if match:
        json_start = payload.find("{", match.end())
        payload = payload[:match.start()] + (
            payload[json_start:] if json_start >= 0 else ""
        )
    return payload.strip()


def _first_balanced_json_object(text: str) -> str | None:
    for start, character in enumerate(text):
        if character != "{":
            continue

        depth = 0
        in_string = False
        escaped = False
        for index in range(start, len(text)):
            character = text[index]
            if in_string:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    in_string = False
                continue

            if character == '"':
                in_string = True
            elif character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth == 0:
                    return text[start:index + 1]
    return None


def parse_intent_json(text: str) -> dict[str, Any]:
    payload = _strip_think_blocks(text)
    match = _JSON_FENCE.match(payload)
    payload = match.group(1).strip() if match else payload

    try:
        parsed = json.loads(payload)
    except (json.JSONDecodeError, TypeError) as first_exc:
        candidate = _first_balanced_json_object(payload)
        try:
            if candidate is None:
                raise first_exc
            parsed = json.loads(candidate)
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
