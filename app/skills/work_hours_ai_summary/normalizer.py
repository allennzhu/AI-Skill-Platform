from __future__ import annotations

import json
from typing import Any

_MAX_CHARS = 16000
_MAX_ITEMS = 200
_MAX_TEXT = 400

_ITEM_KEYS = (
    "date",
    "task_name",
    "consumed",
    "hours",
    "user_name",
    "user_id",
    "name",
    "project_name",
    "sj_num",
    "remark",
    "task_process",
    "progress",
    "confirm_status",
    "confirm_status_name",
    "dept_name",
    "demand_name",
    "assigned_to",
    "assigned_to_name",
    "owner_name",
)


def _trim_text(value: Any) -> Any:
    if isinstance(value, str) and len(value) > _MAX_TEXT:
        return value[:_MAX_TEXT] + "…"
    return value


def _slim_row(row: Any) -> dict[str, Any]:
    if not isinstance(row, dict):
        return {}
    out: dict[str, Any] = {}
    for key in _ITEM_KEYS:
        if key in row:
            out[key] = _trim_text(row[key])
    return out


def _slim_list(rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    return [_slim_row(row) for row in rows[:_MAX_ITEMS]]


def normalize(slots: dict[str, Any]) -> dict[str, Any]:
    raw = slots.get("context") or {}
    period = raw.get("period")
    if not isinstance(period, dict):
        period = {}
    if raw.get("date") and not period.get("start_date"):
        period = {
            "start_date": raw.get("date"),
            "end_date": raw.get("date") or period.get("end_date"),
        }

    context: dict[str, Any] = {
        "period": period,
        "filters": raw.get("filters") if isinstance(raw.get("filters"), dict) else {},
        "user_name": raw.get("user_name") or "",
        "total_hours": raw.get("total_hours"),
        "items": _slim_list(raw.get("items")),
        "tasks": _slim_list(raw.get("tasks")),
        "projects": _slim_list(raw.get("projects")),
    }

    payload = json.dumps(context, ensure_ascii=False, default=str)
    if len(payload) > _MAX_CHARS:
        keep = max(20, _MAX_ITEMS // 2)
        context["items"] = context["items"][:keep]
        context["tasks"] = context["tasks"][:keep]
        context["_truncated"] = True
        context["_original_chars"] = len(payload)

    out: dict[str, Any] = {"context": context}
    note = slots.get("user_note")
    if isinstance(note, str) and note.strip():
        out["user_note"] = note.strip()[:2000]
    scope = slots.get("scope")
    if scope in ("personal", "department"):
        out["scope"] = scope
    else:
        names = {
            str(row.get("user_name") or "").strip()
            for row in (context["items"] + context["tasks"])
            if isinstance(row, dict)
        }
        names.discard("")
        out["scope"] = "department" if len(names) > 1 else "personal"
    return out
