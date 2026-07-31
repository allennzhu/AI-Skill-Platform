from typing import Any


def build_response(result: dict[str, Any]) -> dict[str, Any]:
    skills = result.get("skills") or []
    skills_text = "、".join(skills) if isinstance(skills, list) else str(skills)
    reply = "服务正常。"
    if skills_text:
        reply = f"服务正常。可用技能：{skills_text}"
    return {"result": result, "reply": reply}
