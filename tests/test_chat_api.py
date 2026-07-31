from fastapi.testclient import TestClient

from app.llm.client import FakeLLMClient
from app.main import create_app


def test_chat_echo_with_fake_llm():
    fake = FakeLLMClient('{"intent":"echo","slots":{"text":"hello"}}')
    client = TestClient(create_app(llm_client=fake))
    response = client.post("/v1/chat", json={"message": "say hello"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["result"]["echo"] == "hello"


def test_chat_need_slot():
    fake = FakeLLMClient('{"intent":"echo","slots":{}}')
    client = TestClient(create_app(llm_client=fake))
    response = client.post("/v1/chat", json={"message": "echo something"})

    assert response.status_code == 200
    assert response.json()["status"] == "need_slot"


def test_chat_llm_error():
    fake = FakeLLMClient("NOT_JSON")
    client = TestClient(create_app(llm_client=fake))
    response = client.post("/v1/chat", json={"message": "hi"})

    assert response.status_code == 200
    assert response.json()["status"] == "llm_error"


def test_chat_rejects_blank_message():
    fake = FakeLLMClient('{"intent":"echo","slots":{"text":"unused"}}')
    client = TestClient(create_app(llm_client=fake))
    response = client.post("/v1/chat", json={"message": "   "})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "bad_request"
