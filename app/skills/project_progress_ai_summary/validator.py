from typing import Any


def validate(slots: dict[str, Any]) -> None:
    if "context" not in slots or slots["context"] is None:
        raise ValueError("context required")
    if not isinstance(slots["context"], dict):
        raise ValueError("context must be an object")
