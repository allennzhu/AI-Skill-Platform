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


def test_request_validation_error_shape():
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/items/{item_id}")
    def get_item(item_id: int):
        return {"item_id": item_id}

    response = TestClient(app).get("/items/not-an-integer")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "bad_request"


def test_unhandled_exception_shape():
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom")
    def boom():
        raise RuntimeError("private failure details")

    response = TestClient(app, raise_server_exceptions=False).get("/boom")

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "internal_error",
            "message": "Internal server error",
            "details": {},
        }
    }
