from typing import Any

_EMPTY_ANALYSIS: dict[str, Any] = {
    "answer": "",
    "dimensions": [],
    "heatmap_findings": [],
    "saturation_summary": "",
    "suggestions": [],
}


def build_response(result: dict[str, Any]) -> dict[str, Any]:
    result = result or {}
    analysis = result.get("analysis") or dict(_EMPTY_ANALYSIS)
    return {
        "result": {
            "analysis": analysis,
            "question": result.get("question") or "",
            "period": result.get("period"),
            "context_keys": result.get("context_keys") or [],
        },
        # reply 供对话式调用兜底展示；前端渲染走 result.analysis
        "reply": analysis.get("answer") or "AI 产能分析完成，请查看结果。",
    }
