from typing import Any


def validate(slots: dict[str, Any]) -> None:
    text = slots.get("text")
    if text is None or not isinstance(text, str):
        raise ValueError("text required")
