from __future__ import annotations

import json
from typing import Any

# LLM 上下文预算（字符数）。预算越大 prefill 越慢、越易撞超时；
# 业务侧已确认放宽至 20000（递交归因明细要尽量完整），超出时仍按「保归因明细、砍冗余聚合」的次序降级。
_MAX_CHARS = 20000

# 明细样本条数上限（bug 操作描述/修复备注、延期递交明细）
_MAX_BUG_SAMPLES = 20
_MAX_DELAY_ROWS = 15
_MAX_LIST_ITEMS = 15
_MAX_TEXT = 240


def _trim_text(value: Any) -> Any:
    if isinstance(value, str) and len(value) > _MAX_TEXT:
        return value[:_MAX_TEXT] + "…"
    return value


def _trim_value(value: Any, depth: int = 0) -> Any:
    if depth > 6:
        return "..."
    if isinstance(value, dict):
        return {str(k): _trim_value(v, depth + 1) for k, v in list(value.items())[:60]}
    if isinstance(value, list):
        return [_trim_value(v, depth + 1) for v in value[:_MAX_LIST_ITEMS]]
    return _trim_text(value)


def _pick(source: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    return {k: source[k] for k in keys if k in source}


def _slim_bug_sample(row: dict[str, Any]) -> dict[str, Any]:
    """bug 明细样本只保留分析所需字段：类型/等级/部门归属 + 操作描述与修复备注原文。"""
    keep = _pick(row, [
        "bug_type_name", "bug_level_name", "bug_status_name",
        "project_name", "assigned_to_name", "content", "remark",
        "program_repair_time", "scene_repair_time",
    ])
    return {k: _trim_text(v) for k, v in keep.items()}


def _slim_delay_row(row: dict[str, Any]) -> dict[str, Any]:
    keep = _pick(row, [
        "project_name", "delay_days", "root_cause",
        "duty_role", "duty_person", "problem_brief",
    ])
    return {k: _trim_text(v) for k, v in keep.items()}


def _slim_over_tb_row(row: dict[str, Any]) -> dict[str, Any]:
    """超时递交逐条明细（over_reason 为递交人填写的超时原因，用于归因）。"""
    keep = _pick(row, [
        "project_name", "sj_num", "pro_manager_name",
        "plan_publish_time", "real_publish_time",
        "over_reason", "root_cause", "duty_role", "duty_person", "problem_brief",
    ])
    return {k: _trim_text(v) for k, v in keep.items()}


def _slim_linshi_row(row: dict[str, Any]) -> dict[str, Any]:
    """临时递交逐条明细：重点保留临时原因 linshi_reason 与延期责任人 delay_duty。"""
    keep = _pick(row, [
        "project_name", "sj_num", "pm_name",
        "publish_dijiao_version_name", "plan_publish_time", "real_publish_time",
        "delay_duty", "linshi_reason",
    ])
    return {k: _trim_text(v) for k, v in keep.items()}


def normalize(slots: dict[str, Any]) -> dict[str, Any]:
    raw_ctx = slots.get("context") or {}

    context: dict[str, Any] = {
        "period": raw_ctx.get("period"),
        "filters": raw_ctx.get("filters"),
        "kpi": _trim_value(raw_ctx.get("kpi") or {}),
        "bug": _trim_value(raw_ctx.get("bug") or {}),
        "publish": _trim_value(raw_ctx.get("publish") or {}),
    }

    # 年度目标契约（前端与 skill 约定的既定口径）：体积小、归因价值高，始终保留
    annual_targets = raw_ctx.get("annual_targets")
    if isinstance(annual_targets, dict) and annual_targets:
        context["annual_targets"] = _trim_value(annual_targets)

    delay_detail = raw_ctx.get("delay_detail") or []
    if isinstance(delay_detail, list) and delay_detail:
        context["delay_detail"] = [_slim_delay_row(r) for r in delay_detail[:_MAX_DELAY_ROWS] if isinstance(r, dict)]

    over_tb_detail = raw_ctx.get("over_tb_detail") or []
    if isinstance(over_tb_detail, list) and over_tb_detail:
        context["over_tb_detail"] = [_slim_over_tb_row(r) for r in over_tb_detail[:_MAX_DELAY_ROWS] if isinstance(r, dict)]

    linshi_detail = raw_ctx.get("linshi_detail") or []
    if isinstance(linshi_detail, list) and linshi_detail:
        context["linshi_detail"] = [_slim_linshi_row(r) for r in linshi_detail[:_MAX_DELAY_ROWS] if isinstance(r, dict)]

    bug_samples = raw_ctx.get("bug_samples") or []
    if isinstance(bug_samples, list) and bug_samples:
        context["bug_samples"] = [_slim_bug_sample(r) for r in bug_samples[:_MAX_BUG_SAMPLES] if isinstance(r, dict)]

    # 上一周期总结：只留 process_improve（推进项延续）与 key_matters（跟踪闭环），供 AI 写「延续性」内容
    prev = raw_ctx.get("prev_summary")
    if isinstance(prev, dict) and prev:
        context["prev_summary"] = _trim_value(_pick(prev, ["process_improve", "key_matters"]))

    # 当前周期已有的人工总结：AI 需在其基础上补充而非凭空另起
    curr = raw_ctx.get("current_summary")
    if isinstance(curr, dict) and curr:
        context["current_summary"] = _trim_value(curr)

    # 用户自定义分析提示词：截断防超长/注入，仅作为分析侧重的补充诉求
    user_prompt = raw_ctx.get("user_prompt")
    if isinstance(user_prompt, str) and user_prompt.strip():
        context["user_prompt"] = user_prompt.strip()[:500]

    sections = slots.get("sections") or None

    def _size(ctx: dict[str, Any]) -> int:
        return len(json.dumps(ctx, ensure_ascii=False, default=str))

    # 降级序列：优先砍「冗余聚合」保住「归因明细」——明细（超时/延期/临时原因、BUG 操作描述）是本 skill 归因分析的核心价值
    if _size(context) > _MAX_CHARS and isinstance(context.get("publish"), dict):
        # PM 递交表是纯数字聚合，对归因价值最低，最先砍
        context["publish"].pop("pm_publish_list", None)
    if _size(context) > _MAX_CHARS and isinstance(context.get("bug"), dict):
        for key in ("assignee_top10", "pm_stacks", "project_top10"):
            if isinstance(context["bug"].get(key), list):
                context["bug"][key] = context["bug"][key][:5]
    if _size(context) > _MAX_CHARS and "bug_samples" in context:
        context["bug_samples"] = context["bug_samples"][:10]
    if _size(context) > _MAX_CHARS and isinstance(context.get("bug"), dict):
        for key in ("bug_type_distribution", "self_check_distribution", "h_line_avg_stacks"):
            if isinstance(context["bug"].get(key), list):
                context["bug"][key] = context["bug"][key][:8]
    # 各类明细限条数（归因取样足够，不必全量）
    if _size(context) > _MAX_CHARS:
        for key in ("over_tb_detail", "delay_detail", "linshi_detail"):
            if isinstance(context.get(key), list):
                context[key] = context[key][:8]
    # 仍超：BUG 明细可退化到分布，先砍 bug_samples；递交类归因明细继续保留
    if _size(context) > _MAX_CHARS and "bug_samples" in context:
        context.pop("bug_samples", None)
        context["_bug_samples_dropped"] = True
    # 兜底极限截断：保留归因所需明细（超时/延期/临时原因、BUG 操作描述）与关键分布，只砍冗余聚合
    if _size(context) > _MAX_CHARS:
        src_bug = context.get("bug") or {}
        src_pub = context.get("publish") or {}
        truncated = {
            "period": context.get("period"),
            "filters": context.get("filters"),
            "kpi": context.get("kpi"),
            "bug": {
                "overview": src_bug.get("overview"),
                "bug_type_distribution": src_bug.get("bug_type_distribution"),
                "self_check_distribution": src_bug.get("self_check_distribution"),
            },
            "publish": {
                "overview": src_pub.get("overview"),
                "linshi_distribution": src_pub.get("linshi_distribution"),
                "delay_duty_distribution": src_pub.get("delay_duty_distribution"),
            },
            "_truncated": True,
        }
        # 年度目标契约体积小且是 focus 必填项依据，预算兜底时仍保留
        if context.get("annual_targets"):
            truncated["annual_targets"] = context["annual_targets"]
        for key in ("over_tb_detail", "delay_detail", "linshi_detail"):
            if context.get(key):
                truncated[key] = context[key][:6]
        if context.get("bug_samples"):
            truncated["bug_samples"] = context["bug_samples"][:8]
        # 用户自定义诉求是明确意图，预算兜底时仍保留
        if context.get("user_prompt"):
            truncated["user_prompt"] = context["user_prompt"]
        # 带上明细后仍超预算则逐级回退：先削 bug_samples，再退到仅 overview 的最小集
        if _size(truncated) > _MAX_CHARS and truncated.get("bug_samples"):
            truncated["bug_samples"] = truncated["bug_samples"][:4]
        if _size(truncated) > _MAX_CHARS:
            truncated.pop("bug_samples", None)
        if _size(truncated) > _MAX_CHARS:
            truncated["bug"] = {"overview": src_bug.get("overview")}
            truncated["publish"] = {"overview": src_pub.get("overview")}
        context = truncated

    normalized: dict[str, Any] = {"context": context}
    if sections:
        normalized["sections"] = sections
    return normalized
