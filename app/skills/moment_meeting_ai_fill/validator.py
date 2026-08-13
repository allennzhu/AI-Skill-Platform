from typing import Any


def validate(slots: dict[str, Any]) -> None:
    raw_text = slots.get("raw_text")
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise ValueError("raw_text required")
    if len(raw_text.strip()) < 5:
        raise ValueError("raw_text too short to analyze")

    meet_types = slots.get("meet_types")
    if meet_types is not None and not isinstance(meet_types, dict):
        raise ValueError("meet_types must be an object of {key: label}")

    known_users = slots.get("known_users")
    if known_users is not None and not isinstance(known_users, list):
        raise ValueError("known_users must be an array of nick_name strings")
