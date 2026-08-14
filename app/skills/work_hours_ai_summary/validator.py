from typing import Any


def validate(slots: dict[str, Any]) -> None:
    context = slots.get("context")
    if context is None:
        raise ValueError("context required")
    if not isinstance(context, dict):
        raise ValueError("context must be an object")

    period = context.get("period")
    date = context.get("date")
    has_period = isinstance(period, dict) and (period.get("start_date") or period.get("end_date"))
    if not has_period and not date:
        raise ValueError("context.period.start_date/end_date or context.date required")

    items = context.get("items")
    tasks = context.get("tasks")
    if items is not None and not isinstance(items, list):
        raise ValueError("context.items must be an array")
    if tasks is not None and not isinstance(tasks, list):
        raise ValueError("context.tasks must be an array")
    if items is None and tasks is None:
        raise ValueError("context must contain items or tasks")

    note = slots.get("user_note")
    if note is not None and not isinstance(note, str):
        raise ValueError("user_note must be a string")

    scope = slots.get("scope")
    if scope is not None and scope not in ("personal", "department"):
        raise ValueError("scope must be personal or department")
