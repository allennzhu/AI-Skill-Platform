from typing import Any

from app.api.errors import AppError
from app.skills.base import Skill


class SkillExecutor:
    def run(self, skill: Skill, slots: dict[str, Any]) -> dict[str, Any]:
        try:
            skill.validate(slots)
            normalized = skill.normalize(slots)
            result = skill.execute(normalized)
            return skill.build_response(result)
        except Exception as exc:
            raise AppError(
                code="skill_error",
                message="Skill execution failed",
                details={"reason": str(exc)},
                status_code=500,
            ) from exc
