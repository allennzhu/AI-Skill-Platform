from app.config import Settings
from app.llm.client import HttpLLMClient


def test_http_llm_client_passes_configured_timeout(monkeypatch):
    captured: dict[str, object] = {}

    class Response:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return {"choices": [{"message": {"content": "{}"}}]}

    def fake_post(*args, **kwargs):
        captured.update(kwargs)
        return Response()

    monkeypatch.setattr("app.llm.client.httpx.post", fake_post)
    client = HttpLLMClient(Settings(llm_timeout_seconds=45))

    client.complete("system", "user")

    assert captured["timeout"] == 45


def test_llm_timeout_defaults_to_120_seconds():
    assert Settings().llm_timeout_seconds == 120
