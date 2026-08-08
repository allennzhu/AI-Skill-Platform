from typing import Any

VALID_SECTIONS = {
    "role_reviews",
    "bug_summary",
    "bug_suggestions",
    "focus_items",
    "process_items",
}


def validate(slots: dict[str, Any]) -> None:
    context = slots.get("context")
    if context is None:
        raise ValueError("context required")
    if not isinstance(context, dict):
        raise ValueError("context must be an object")

    period = context.get("period")
    if not isinstance(period, dict) or not period.get("period_key"):
        raise ValueError("context.period with period_type/period_key required")

    # 至少要有一类统计数据，否则 AI 无从分析（禁止无中生有）
    if not any(isinstance(context.get(k), (dict, list)) and context.get(k) for k in ("kpi", "bug", "publish")):
        raise ValueError("context must contain at least one of kpi / bug / publish data")

    sections = slots.get("sections")
    if sections is not None:
        if not isinstance(sections, list):
            raise ValueError("sections must be an array")
        invalid = [s for s in sections if s not in VALID_SECTIONS]
        if invalid:
            raise ValueError(f"invalid sections: {invalid}; valid: {sorted(VALID_SECTIONS)}")
