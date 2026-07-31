from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import yaml


@dataclass
class SkillManifest:
    name: str
    intent: str
    description: str
    required_slots: list[str]


@runtime_checkable
class Skill(Protocol):
    def validate(self, slots: dict[str, Any]) -> None: ...

    def normalize(self, slots: dict[str, Any]) -> dict[str, Any]: ...

    def execute(self, slots: dict[str, Any]) -> dict[str, Any]: ...

    def build_response(self, result: dict[str, Any]) -> dict[str, Any]: ...


class _LoadedSkill:
    def __init__(
        self,
        validator: Any,
        normalizer: Any,
        executor: Any,
        response: Any,
    ) -> None:
        self._validator = validator
        self._normalizer = normalizer
        self._executor = executor
        self._response = response

    def validate(self, slots: dict[str, Any]) -> None:
        self._validator.validate(slots)

    def normalize(self, slots: dict[str, Any]) -> dict[str, Any]:
        return self._normalizer.normalize(slots)

    def execute(self, slots: dict[str, Any]) -> dict[str, Any]:
        return self._executor.execute(slots)

    def build_response(self, result: dict[str, Any]) -> dict[str, Any]:
        return self._response.build_response(result)


def _load_module(skill_dir: Path, module_name: str) -> Any:
    path = skill_dir / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(
        f"skill.{skill_dir.name}.{module_name}",
        path,
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load skill module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _parse_manifest(skill_dir: Path) -> SkillManifest:
    manifest_path = skill_dir / "manifest.yaml"
    with manifest_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    required = data.get("slots", {}).get("required", [])
    required_slots = [slot["name"] for slot in required]
    return SkillManifest(
        name=data["name"],
        intent=data["intent"],
        description=data["description"],
        required_slots=required_slots,
    )


def load_skill_package(path: Path) -> tuple[SkillManifest, Skill]:
    skill_dir = path.resolve()
    manifest = _parse_manifest(skill_dir)
    validator = _load_module(skill_dir, "validator")
    normalizer = _load_module(skill_dir, "normalizer")
    executor = _load_module(skill_dir, "executor")
    response = _load_module(skill_dir, "response")
    skill = _LoadedSkill(validator, normalizer, executor, response)
    return manifest, skill
