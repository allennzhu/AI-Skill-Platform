from __future__ import annotations

import json
from typing import Any

# LLM 上下文预算（字符数）。工程产能分析的核心价值在「资源热力图归因」，
# 故降级时优先砍冗余聚合与人员画像，最后才动「极端异常单日」明细。
_MAX_CHARS = 16000

_MAX_PROFILES = 60          # 人员画像上限（周期>1月抽样后一般已收敛）
_MAX_EXTREME = 40           # 单日≥12h 极端异常条目上限（始终尽量保留）
_MAX_TASKS_PER_DAY = 8      # 每个极端单日附带的任务明细条数
_MAX_TEXT = 200


def _trim_text(value: Any) -> Any:
    if isinstance(value, str) and len(value) > _MAX_TEXT:
        return value[:_MAX_TEXT] + "…"
    return value


def _pick(source: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    return {k: source[k] for k in keys if k in source}


def _slim_profile(row: dict[str, Any]) -> dict[str, Any]:
    keep = _pick(row, [
        "name", "dept", "hire_type",
        "week_total", "avg_daily",
        "project_ratio", "non_project_ratio", "leave_ratio",
        "overload_days", "optimal_days", "insufficient_days", "idle_days", "overtime_days",
    ])
    return {k: _trim_text(v) for k, v in keep.items()}


def _slim_task(row: dict[str, Any]) -> dict[str, Any]:
    keep = _pick(row, ["name", "project_name", "hours", "type"])
    return {k: _trim_text(v) for k, v in keep.items()}


def _slim_extreme(row: dict[str, Any]) -> dict[str, Any]:
    out = _pick(row, [
        "person", "dept", "day", "hours",
        "project_hours", "non_project_hours", "leave_hours",
    ])
    tasks = row.get("tasks")
    if isinstance(tasks, list) and tasks:
        out["tasks"] = [_slim_task(t) for t in tasks[:_MAX_TASKS_PER_DAY] if isinstance(t, dict)]
    return {k: (_trim_text(v) if not isinstance(v, list) else v) for k, v in out.items()}


def normalize(slots: dict[str, Any]) -> dict[str, Any]:
    raw_ctx = slots.get("context") or {}

    context: dict[str, Any] = {
        "period": raw_ctx.get("period"),
        "filters": raw_ctx.get("filters"),
        "capacity_overview": raw_ctx.get("capacity_overview") or {},
    }

    trend = raw_ctx.get("trend") or []
    if isinstance(trend, list) and trend:
        context["trend"] = trend

    heatmap = raw_ctx.get("heatmap") or {}
    if isinstance(heatmap, dict) and heatmap:
        slim_heatmap: dict[str, Any] = {}
        if isinstance(heatmap.get("saturation_summary"), dict):
            slim_heatmap["saturation_summary"] = heatmap["saturation_summary"]
        profiles = heatmap.get("person_profiles") or []
        if isinstance(profiles, list) and profiles:
            slim_heatmap["person_profiles"] = [
                _slim_profile(r) for r in profiles[:_MAX_PROFILES] if isinstance(r, dict)
            ]
        extremes = heatmap.get("extreme_days") or []
        if isinstance(extremes, list) and extremes:
            slim_heatmap["extreme_days"] = [
                _slim_extreme(r) for r in extremes[:_MAX_EXTREME] if isinstance(r, dict)
            ]
        context["heatmap"] = slim_heatmap

    question = slots.get("question")
    if isinstance(question, str) and question.strip():
        context["question"] = question.strip()[:500]

    def _size(ctx: dict[str, Any]) -> int:
        return len(json.dumps(ctx, ensure_ascii=False, default=str))

    hm = context.get("heatmap") or {}

    # 降级序列：先砍冗余聚合，最后才砍热力图极端异常明细
    if _size(context) > _MAX_CHARS and isinstance(hm.get("person_profiles"), list):
        hm["person_profiles"] = hm["person_profiles"][:30]
    if _size(context) > _MAX_CHARS and isinstance(context.get("trend"), list):
        context["trend"] = context["trend"][:12]
    if _size(context) > _MAX_CHARS and isinstance(hm.get("extreme_days"), list):
        for row in hm["extreme_days"]:
            if isinstance(row.get("tasks"), list):
                row["tasks"] = row["tasks"][:4]
    if _size(context) > _MAX_CHARS and isinstance(hm.get("person_profiles"), list):
        hm["person_profiles"] = hm["person_profiles"][:15]
    # 兜底：极端异常条目最后才削，但始终保留（这是热力图归因的立身之本）
    if _size(context) > _MAX_CHARS and isinstance(hm.get("extreme_days"), list):
        hm["extreme_days"] = hm["extreme_days"][:20]
        context["_truncated"] = True

    normalized: dict[str, Any] = {"context": context}
    if isinstance(question, str) and question.strip():
        normalized["question"] = question.strip()[:500]
    return normalized
