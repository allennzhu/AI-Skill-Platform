from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.errors import AppError, register_exception_handlers

def test_app_error_shape():
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom")
    def boom():
        raise AppError(code="bad_request", message="missing field", details={"field": "message"})

    r = TestClient(app).get("/boom")
    assert r.status_code == 400
    body = r.json()
    assert body["error"]["code"] == "bad_request"
    assert body["error"]["message"] == "missing field"
    assert body["error"]["details"]["field"] == "message"
