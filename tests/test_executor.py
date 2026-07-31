from pathlib import Path

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.api.errors import AppError
from app.main import create_app
from app.runtime.executor import SkillExecutor
from app.runtime.registry import SkillRegistry
from app.runtime.service import RuntimeService
from app.runtime.session import SessionStore


def make_runtime() -> RuntimeService:
    root = Path(__file__).resolve().parents[1] / "app" / "skills"
    return RuntimeService(
        registry=SkillRegistry.load_dir(root),
        sessions=SessionStore(ttl_seconds=3600),
    )


def test_executor_runs_skill_pipeline_in_order() -> None:
    calls: list[str] = []

    class RecordingSkill:
        def validate(self, slots: dict) -> None:
            calls.append("validate")

        def normalize(self, slots: dict) -> dict:
            calls.append("normalize")
            return {"text": slots["text"].strip()}

        def execute(self, slots: dict) -> dict:
            calls.append("execute")
            return {"echo": slots["text"]}

        def build_response(self, result: dict) -> dict:
            calls.append("build_response")
            return result

    result = SkillExecutor().run(RecordingSkill(), {"text": " hi "})

    assert result == {"echo": "hi"}
    assert calls == ["validate", "normalize", "execute", "build_response"]


def test_executor_wraps_skill_exceptions() -> None:
    class FailingSkill:
        def validate(self, slots: dict) -> None:
            raise ValueError("bad input")

        def normalize(self, slots: dict) -> dict:
            return slots

        def execute(self, slots: dict) -> dict:
            return slots

        def build_response(self, result: dict) -> dict:
            return result

    with pytest.raises(AppError) as exc_info:
        SkillExecutor().run(FailingSkill(), {})

    assert exc_info.value.code == "skill_error"
    assert exc_info.value.status_code == 500
    assert exc_info.value.details == {}


def test_executor_preserves_app_error() -> None:
    expected = AppError(
        code="bad_request",
        message="invalid skill input",
        details={"field": "text"},
        status_code=422,
    )

    class AppErrorSkill:
        def validate(self, slots: dict) -> None:
            raise expected

        def normalize(self, slots: dict) -> dict:
            return slots

        def execute(self, slots: dict) -> dict:
            return slots

        def build_response(self, result: dict) -> dict:
            return result

    with pytest.raises(AppError) as exc_info:
        SkillExecutor().run(AppErrorSkill(), {})

    assert exc_info.value is expected


def test_runtime_echo_ok() -> None:
    result = make_runtime().run(intent="echo", slots={"text": "hi"}, session_id=None)

    assert result.status == "ok"
    assert result.result == {"echo": "hi"}


def test_runtime_echo_need_slot() -> None:
    result = make_runtime().run(intent="echo", slots={}, session_id=None)

    assert result.status == "need_slot"
    assert result.missing_slots == ["text"]
    assert result.reply == "请补充: text"


def test_runtime_unknown_intent_returns_result() -> None:
    result = make_runtime().run(intent="unknown", slots={}, session_id=None)

    assert result.status == "unknown_intent"
    assert result.intent == "unknown"
    assert result.slots == {}


def test_runtime_merges_slots_from_session() -> None:
    runtime = make_runtime()
    first = runtime.run(intent="echo", slots={}, session_id=None)

    result = runtime.run(
        intent="echo",
        slots={"text": "later"},
        session_id=first.session_id,
    )

    assert result.status == "ok"
    assert result.slots == {"text": "later"}
    assert result.result == {"echo": "later"}


def test_create_app_builds_runtime_synchronously() -> None:
    app = create_app()

    assert isinstance(app.state.runtime, RuntimeService)
    assert (
        app.state.runtime.sessions.ttl_seconds
        == app.state.settings.session_ttl_seconds
    )


def test_get_runtime_reads_app_state() -> None:
    from app.api.deps import get_runtime

    app = FastAPI()
    expected = object()
    app.state.runtime = expected

    @app.get("/runtime")
    def runtime_endpoint(request: Request) -> dict[str, bool]:
        return {"matches": get_runtime(request) is expected}

    response = TestClient(app).get("/runtime")

    assert response.json() == {"matches": True}
