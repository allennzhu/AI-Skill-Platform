import pytest

from app.api.errors import AppError
from app.llm.parse import parse_intent_json


def test_parse_plain_json():
    assert parse_intent_json('{"intent":"echo","slots":{"text":"x"}}')["intent"] == "echo"


def test_parse_fenced_json():
    raw = '```json\n{"intent":"echo","slots":{}}\n```'
    assert parse_intent_json(raw)["slots"] == {}


def test_parse_invalid():
    with pytest.raises(AppError) as exc_info:
        parse_intent_json("not json")

    assert exc_info.value.code == "llm_error"
