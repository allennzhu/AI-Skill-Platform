from typing import Any


def normalize(slots: dict[str, Any]) -> dict[str, Any]:
    return {"text": slots["text"]}
