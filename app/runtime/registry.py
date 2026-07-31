from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.skills.base import Skill, SkillManifest, load_skill_package


@dataclass
class RegisteredSkill:
    manifest: SkillManifest
    skill: Skill


class SkillRegistry:
    def __init__(self, skills: dict[str, RegisteredSkill] | None = None) -> None:
        self._skills = skills or {}

    @classmethod
    def load_dir(cls, skills_root: Path) -> SkillRegistry:
        skills: dict[str, RegisteredSkill] = {}
        root = skills_root.resolve()
        for child in sorted(root.iterdir()):
            if not child.is_dir():
                continue
            manifest_path = child / "manifest.yaml"
            if not manifest_path.is_file():
                continue
            manifest, skill = load_skill_package(child)
            if manifest.intent == "unknown":
                continue
            skills[manifest.intent] = RegisteredSkill(manifest=manifest, skill=skill)
        return cls(skills)

    def get(self, intent: str) -> RegisteredSkill | None:
        return self._skills.get(intent)

    def list_intents(self) -> list[str]:
        return sorted(self._skills.keys())
