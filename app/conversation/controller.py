from app.api.errors import AppError
from app.llm.client import LLMClient
from app.llm.credentials import get_request_llm_client
from app.llm.parse import parse_intent_json
from app.llm.prompt import build_system_prompt
from app.models.runtime import RuntimeResult
from app.runtime.service import RuntimeService


class ConversationController:
    def __init__(self, runtime: RuntimeService, llm: LLMClient) -> None:
        self.runtime = runtime
        self.llm = llm

    def handle_chat(
        self,
        message: str,
        session_id: str | None,
    ) -> RuntimeResult:
        if not message or not message.strip():
            raise AppError("bad_request", "message is required")

        system = build_system_prompt(self.runtime.registry.prompt_catalog())
        try:
            # Prefer per-request credentials (user key); fall back to injected client for unit tests.
            try:
                client = get_request_llm_client()
            except AppError as exc:
                if exc.code != "unauthorized":
                    raise
                client = self.llm
            raw = client.complete(system, message)
            parsed = parse_intent_json(raw)
        except AppError as exc:
            if exc.code != "llm_error":
                raise
            session = (
                self.runtime.sessions.get(session_id)
                if session_id
                else None
            )
            if session is None:
                session = self.runtime.sessions.create(session_id)
            return RuntimeResult(
                session_id=session.session_id,
                status="llm_error",
                reply=exc.message,
            )

        return self.runtime.run(
            parsed["intent"],
            parsed.get("slots") or {},
            session_id,
        )
