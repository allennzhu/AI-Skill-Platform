from typing import Any


def build_system_prompt(
    intents_doc: str,
    today: str | None = None,
    pending_intent: str | None = None,
    pending_slots: dict[str, Any] | None = None,
    missing_slots: list[str] | None = None,
) -> str:
    today_line = f"Today's date is {today}. Convert relative dates (this week, last week, first half of year, 上半年, 今天) to YYYY-MM-DD.\n" if today else ""
    pending_lines = ""
    if pending_intent:
        pending_lines = (
            "This is a multi-turn conversation.\n"
            f"Current intent: {pending_intent}\n"
            f"Already collected slots: {pending_slots or {}}\n"
            f"Still missing required slots: {missing_slots or []}\n"
            "Keep the current intent unless the user clearly starts a different task. "
            "A short reply like a name, department alias (e.g. 场景C), or a date is slot filling, not a new intent.\n"
        )
    return (
        "You route user messages to supported skills.\n"
        "Return only a JSON object with this exact shape: "
        '{"intent":"<intent name>","slots":{}}.\n'
        "Do not include Markdown fences or explanatory text.\n"
        f"{today_line}"
        f"{pending_lines}"
        "Rules:\n"
        "- Choose the best matching intent from the catalog. If none fit, use intent \"unknown\" and empty slots.\n"
        "- Fill slots you can extract from the user message. Omit slots you cannot extract.\n"
        "- Never invent backend-assembled slots such as context / items / KPI payloads.\n"
        "- person_name and dept_name should be the words the user said (aliases like 场景c are OK).\n"
        "- Put extra instructions (打分, 重点) into user_note or question when those slots exist.\n\n"
        "Supported intents:\n"
        f"{intents_doc.strip()}"
    )
