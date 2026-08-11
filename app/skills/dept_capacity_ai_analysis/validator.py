from typing import Any


def validate(slots: dict[str, Any]) -> None:
    context = slots.get("context")
    if context is None:
        raise ValueError("context required")
    if not isinstance(context, dict):
        raise ValueError("context must be an object")

    period = context.get("period")
    if not isinstance(period, dict) or not period.get("start_date") or not period.get("end_date"):
        raise ValueError("context.period with start_date/end_date required")

    # 至少要有产能总览或热力图数据，否则无从分析（禁止无中生有）
    if not any(isinstance(context.get(k), (dict, list)) and context.get(k)
               for k in ("capacity_overview", "trend", "heatmap")):
        raise ValueError("context must contain at least one of capacity_overview / trend / heatmap")

    question = slots.get("question")
    if question is not None and not isinstance(question, str):
        raise ValueError("question must be a string")
