from pathlib import Path

from app.skills.base import load_skill_package

ROOT = Path(__file__).resolve().parents[1] / "app" / "skills"


def test_echo_skill_executes():
    manifest, skill = load_skill_package(ROOT / "echo")
    assert manifest.intent == "echo"
    assert manifest.required_slots == ["text"]
    skill.validate({"text": "hi"})
    slots = skill.normalize({"text": "hi"})
    result = skill.execute(slots)
    payload = skill.build_response(result)
    assert payload["result"] == {"echo": "hi"}


def test_health_skill_lists_skills():
    _, skill = load_skill_package(ROOT / "health")
    payload = skill.build_response(skill.execute({}))
    assert payload["result"]["runtime"] == "ok"
    assert "echo" in payload["result"]["skills"]
