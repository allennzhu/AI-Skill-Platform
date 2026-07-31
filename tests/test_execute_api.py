from fastapi.testclient import TestClient

from app.main import create_app


def test_execute_echo():
    client = TestClient(create_app())
    r = client.post("/v1/execute", json={"intent": "echo", "slots": {"text": "hi"}})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["result"]["echo"] == "hi"


def test_execute_need_slot():
    client = TestClient(create_app())
    r = client.post("/v1/execute", json={"intent": "echo", "slots": {}})
    assert r.status_code == 200
    assert r.json()["status"] == "need_slot"
    assert r.json()["missing_slots"] == ["text"]


def test_execute_health():
    client = TestClient(create_app())
    r = client.post("/v1/execute", json={"intent": "health", "slots": {}})
    assert r.status_code == 200
    assert r.json()["result"]["runtime"] == "ok"
