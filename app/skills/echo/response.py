from typing import Any


def build_response(result: dict[str, Any]) -> dict[str, Any]:
    return {"result": result, "reply": f"echo: {result['echo']}"}
