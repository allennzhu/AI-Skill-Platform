from app.runtime.registry import SkillRegistry
from app.runtime.session import SessionStore
from app.runtime.service import RuntimeService
from app.llm.client import FakeLLMClient
from pathlib import Path
from app.main import create_app
from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1] / "app" / "skills"


def test_registry_includes_qa_board_analysis():
    reg = SkillRegistry.load_dir(ROOT)
    assert "qa_board_analysis" in reg.list_intents()


def test_execute_qa_board_analysis_with_fake_llm(monkeypatch):
    fake = FakeLLMClient(
        "本月缺陷总量与递交表现整体可控，致命与严重问题集中在少数部门，"
        "建议优先关注高密度项目并跟进延期递交原因，同时结合总结事项推进改进。"
    )
    client = TestClient(create_app(llm_client=fake))

    # Skill builds its own HttpLLMClient; monkeypatch get_settings path by
    # patching HttpLLMClient.complete used inside the skill.
    from app.llm import client as llm_mod

    def _fake_complete(self, system, user):
        return fake.complete(system, user)

    monkeypatch.setattr(llm_mod.HttpLLMClient, "complete", _fake_complete)

    r = client.post(
        "/v1/execute",
        json={
            "intent": "qa_board_analysis",
            "slots": {
                "context": {
                    "period": {"type": "month", "key": "2026-07"},
                    "kpi": {"total": 10},
                    "bug": {"overview": {"total": 10}},
                    "publish": {"overview": {}},
                    "summary": {"items": []},
                }
            },
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["intent"] == "qa_board_analysis"
    assert "缺陷总量" in (body.get("reply") or "")
    assert "缺陷总量" in (body.get("result") or {}).get("reply", "")
