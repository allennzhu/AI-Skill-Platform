from typing import Any

from app.api.errors import AppError
from app.llm.client import LLMClient
from app.llm.credentials import get_request_llm_client
from app.llm.parse import parse_intent_json
from app.llm.prompt import build_system_prompt
from app.models.runtime import RuntimeResult
from app.runtime.service import RuntimeService


class ConversationController:
    def __init__(self, runtime: RuntimeService, llm: LLMClient | None = None) -> None:
        self.runtime = runtime
        self.llm = llm

    def _parse_message(
        self,
        message: str,
        session_id: str | None,
        today: str | None = None,
    ) -> RuntimeResult | dict[str, Any]:
        if not message or not message.strip():
            raise AppError("bad_request", "message is required")

        pending = self.runtime.sessions.get(session_id) if session_id else None
        pending_intent = pending.intent if pending else None
        pending_slots = dict(pending.slots) if pending else None
        missing_slots = None
        if pending and pending.intent:
            registered = self.runtime.registry.get(pending.intent)
            if registered:
                missing_slots = self.runtime.slot_manager.missing(
                    registered.manifest.required_slots,
                    pending.slots,
                )

        system = build_system_prompt(
            self.runtime.registry.prompt_catalog(),
            today=today,
            pending_intent=pending_intent,
            pending_slots=pending_slots,
            missing_slots=missing_slots,
        )
        try:
            client = self.llm or get_request_llm_client()
            raw = client.complete(system, message)
            return parse_intent_json(raw)
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

    def handle_chat(
        self,
        message: str,
        session_id: str | None,
        today: str | None = None,
    ) -> RuntimeResult:
        parsed = self._parse_message(message, session_id, today)
        if isinstance(parsed, RuntimeResult):
            return parsed
        return self.runtime.run(
            parsed["intent"],
            parsed.get("slots") or {},
            session_id,
        )

    def handle_route(
        self,
        message: str,
        session_id: str | None,
        today: str | None = None,
    ) -> RuntimeResult:
        parsed = self._parse_message(message, session_id, today)
        if isinstance(parsed, RuntimeResult):
            return parsed
        return self.runtime.route(
            parsed["intent"],
            parsed.get("slots") or {},
            session_id,
        )
