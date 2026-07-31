import logging
from typing import Any

from app.api.errors import AppError
from app.skills.base import Skill

logger = logging.getLogger(__name__)


class SkillExecutor:
    def run(self, skill: Skill, slots: dict[str, Any]) -> dict[str, Any]:
        try:
            skill.validate(slots)
            normalized = skill.normalize(slots)
            result = skill.execute(normalized)
            return skill.build_response(result)
        except AppError:
            raise
        except Exception as exc:
            logger.exception("Skill execution failed")
            raise AppError(
                code="skill_error",
                message="Skill execution failed",
                status_code=500,
            ) from exc
