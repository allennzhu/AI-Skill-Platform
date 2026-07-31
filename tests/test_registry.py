from pathlib import Path

import pytest

from app.api.errors import AppError
from app.runtime.registry import SkillRegistry
from app.runtime.router import Router

ROOT = Path(__file__).resolve().parents[1] / "app" / "skills"


def test_registry_loads_echo_and_health():
    reg = SkillRegistry.load_dir(ROOT)
    assert set(reg.list_intents()) >= {"echo", "health"}


def test_router_unknown_intent():
    reg = SkillRegistry.load_dir(ROOT)
    router = Router(reg)
    with pytest.raises(AppError) as ei:
        router.resolve("nope")
    assert ei.value.code == "unknown_intent"


def test_router_literal_unknown_intent():
    reg = SkillRegistry.load_dir(ROOT)
    router = Router(reg)
    with pytest.raises(AppError) as ei:
        router.resolve("unknown")
    assert ei.value.code == "unknown_intent"
