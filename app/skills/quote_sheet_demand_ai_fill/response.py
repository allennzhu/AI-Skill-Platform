from typing import Any

_EMPTY_QUOTE_DEMAND: dict[str, Any] = {
    "demand_name": "",
    "description": "",
    "amount": 0,
    "unit": "",
    "version": "",
    "assigned_to_name": "",
    "start_date": "",
    "end_date": "",
    "missing_fields": [],
}


def build_response(result: dict[str, Any]) -> dict[str, Any]:
    result = result or {}
    demands = result.get("quote_demands")
    if not isinstance(demands, list) or not demands:
        demand = result.get("quote_demand") or dict(_EMPTY_QUOTE_DEMAND)
        demands = [demand]
    names = [str(item.get("demand_name") or "").strip() for item in demands if isinstance(item, dict)]
    names = [name for name in names if name]
    reply = "、".join(names[:5]) if names else "AI 已完成报价单需求抽取，请查看回填结果。"
    if len(names) > 5:
        reply += f" 等共 {len(names)} 条"
    return {
        "result": {
            "version": result.get("version") or "",
            "quote_demands": demands,
        },
        "reply": reply,
    }
