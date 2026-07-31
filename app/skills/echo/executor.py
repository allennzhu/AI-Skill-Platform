from typing import Any


def execute(slots: dict[str, Any]) -> dict[str, Any]:
    return {"echo": slots["text"]}
