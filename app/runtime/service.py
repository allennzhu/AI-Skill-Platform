from typing import Any

from app.api.errors import AppError
from app.models.runtime import RuntimeResult
from app.runtime.executor import SkillExecutor
from app.runtime.registry import SkillRegistry
from app.runtime.router import Router
from app.runtime.session import SessionStore
from app.runtime.slot_manager import SlotManager


class RuntimeService:
    def __init__(
        self,
        registry: SkillRegistry,
        sessions: SessionStore,
        router: Router | None = None,
        slot_manager: SlotManager | None = None,
        executor: SkillExecutor | None = None,
    ) -> None:
        self.registry = registry
        self.sessions = sessions
        self.router = router or Router(registry)
        self.slot_manager = slot_manager or SlotManager()
        self.executor = executor or SkillExecutor()

    def run(
        self,
        intent: str,
        slots: dict[str, Any],
        session_id: str | None,
    ) -> RuntimeResult:
        session = self.sessions.get(session_id) if session_id else None
        if session is None:
            session = self.sessions.create(session_id)

        self.sessions.merge_slots(session, intent, slots)

        try:
            registered = self.router.resolve(intent)
        except AppError as exc:
            if exc.code != "unknown_intent":
                raise
            self.sessions.save(session)
            return RuntimeResult(
                session_id=session.session_id,
                status="unknown_intent",
                intent=intent,
                slots=dict(session.slots),
            )

        missing_slots = self.slot_manager.missing(
            registered.manifest.required_slots,
            session.slots,
        )
        if missing_slots:
            self.sessions.save(session)
            return RuntimeResult(
                session_id=session.session_id,
                status="need_slot",
                intent=intent,
                slots=dict(session.slots),
                missing_slots=missing_slots,
                reply=f"请补充: {', '.join(missing_slots)}",
            )

        response = self.executor.run(registered.skill, session.slots)
        self.sessions.save(session)
        return RuntimeResult(
            session_id=session.session_id,
            status="ok",
            intent=intent,
            slots=dict(session.slots),
            result=response.get("result"),
            reply=response.get("reply"),
        )
