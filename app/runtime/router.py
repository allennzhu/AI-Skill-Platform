from __future__ import annotations

from app.api.errors import AppError
from app.runtime.registry import RegisteredSkill, SkillRegistry


class Router:
    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry

    def resolve(self, intent: str) -> RegisteredSkill:
        if intent == "unknown":
            raise AppError(code="unknown_intent", message=f"Unknown intent: {intent}")
        registered = self._registry.get(intent)
        if registered is None:
            raise AppError(code="unknown_intent", message=f"Unknown intent: {intent}")
        return registered
