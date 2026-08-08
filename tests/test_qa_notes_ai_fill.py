import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.llm.client import FakeLLMClient
from app.main import create_app
from app.runtime.registry import SkillRegistry

ROOT = Path(__file__).resolve().parents[1] / "app" / "skills"

_FAKE_NOTES = {
    "role_reviews": [
        {
            "role": "QA",
            "problem": "未自检占比偏高",
            "suggestion": "推动自检清单落地",
        }
    ],
    "bug_summary": (
        "本期缺陷总量整体可控，致命与严重占比达标，"
        "类型以功能类为主，未自检仍需关注，高发集中在少数项目。"
    ),
    "bug_suggestions": {
        "art": "本期该侧无突出问题，保持现状",
        "program": "关注功能类缺陷回归",
        "qa": "强化自检闭环",
    },
    "focus_items": [
        {
            "title": "自检闭环",
            "duty_role": "QA",
            "conclusion": "推进自检清单落地并复盘",
        }
    ],
    "process_items": [],
}


def test_registry_includes_qa_notes_ai_fill():
    reg = SkillRegistry.load_dir(ROOT)
    assert "qa_notes_ai_fill" in reg.list_intents()


def test_execute_qa_notes_ai_fill_with_fake_llm(monkeypatch):
    fake = FakeLLMClient(json.dumps(_FAKE_NOTES, ensure_ascii=False))
    client = TestClient(create_app(llm_client=fake))

    from app.llm import client as llm_mod

    def _fake_complete(self, system, user):
        return fake.complete(system, user)

    monkeypatch.setattr(llm_mod.HttpLLMClient, "complete", _fake_complete)

    r = client.post(
        "/v1/execute",
        json={
            "intent": "qa_notes_ai_fill",
            "slots": {
                "context": {
                    "period": {"period_type": "month", "period_key": "2026-07"},
                    "kpi": {"summary": {"bug_total": {"value": 10}}},
                    "bug": {"overview": {"total": 10}},
                    "publish": {"overview": {}},
                }
            },
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["intent"] == "qa_notes_ai_fill"
    notes = (body.get("result") or {}).get("notes") or {}
    assert "未自检" in (notes.get("bug_summary") or "")
    assert notes.get("role_reviews")
    assert "未自检" in (body.get("reply") or "")
