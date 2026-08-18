from __future__ import annotations

import json
import re
from typing import Any

from app.api.errors import AppError
from app.llm.credentials import get_request_llm_client

_THINK_RE = re.compile(r"<think>[\s\S]*?</think>", re.IGNORECASE)
_THINK_UNCLOSED_RE = re.compile(r"<think>[\s\S]*$", re.IGNORECASE)

# 会议内容表单校验上限为 2000 字符，留出余量截断到 1800，避免回填后前端校验不通过。
_MAX_CONTENT = 1800
_MAX_TODO_TEXT = 500
_MAX_TODOS = 30
_MAX_ATTENDEES = 60
_MAX_NAME_LEN = 40

SYSTEM_PROMPT = """你是「项目动态-会议动态」的信息抽取助手。用户会粘贴一段会议纪要原文
（可能来自飞书/企微智能纪要，含水印、AI 免责声明、图片 markdown、待办清单、相关链接等）。
你的任务是从原文中抽取「会议动态」表单所需的结构化字段，供前端直接回填。

你会收到一段 JSON 输入：
- raw_text：会议纪要原文（唯一事实来源，所有输出必须来自它，禁止编造）
- meet_types（可选）：会议类型候选 {key: 名称}，你只能从 key 中选一个最贴切的返回，或返回空串
- known_users（可选）：系统内已知的人员昵称列表，仅用于把原文里提到的人「规范化」为列表中
  完全一致的昵称（例如原文写「@华中豪」而列表里正是「华中豪」）；不得据此臆造原文没提到的人

输出一个 JSON 对象，结构严格如下：

{
  "type": "<从 meet_types 的 key 中选最贴切的一个；无把握则空串 \\"\\">",
  "content": "<仅删除无关噪声后的会议内容原文（逐字保留，不改写）>",
  "attendees": ["参会人姓名", "..."],
  "todos": [
    { "text": "待办事项内容（含背景/要求，一句到数句）", "assignees": ["责任人姓名", "..."] }
  ]
}

硬性规则（违反任一条即为不合格）：
1. 只输出上述 JSON 对象本身，禁止 Markdown、代码块围栏、解释文字或 <think> 内容。
2. type：仅当某个 meet_types 的 key 语义明显匹配会议主题时才返回该 key；模棱两可或没有合适项
   时返回空串 ""。禁止返回不在 meet_types 里的值，禁止返回名称（label），只能返回 key。
   未提供 meet_types 时一律返回 ""。
3. content：【原文逐字搬运，严禁笡改】——content 必须是「把原文中与会议完全无关的噪声删掉后剩下的部分」，其余一字不改：
   - 【绝对禁止】改写、润色、概括、归纳、拆分合并句子、调整语序、替换措辞、同义改写、增删标点——
     保留原文的每一句话、每一个用词、标点与分段，一字不改（哪怕你觉得有错别字/不通顺也不准改）；
   - 仅允许「整段删除」以下与会议内容完全无关的噪声（只能删，删完不动其余文字）：
     水印句（如「暂时无法在五一视界文档外展示此内容」）、AI 免责声明（如「智能会议纪要由 AI 生成，可能不准确…」）、
     图片 markdown（![](...)）、「相关链接 / 文字记录」等纯占位标题及其下链接；
   - 「会议主题 / 会议时间 / 参会人」等头部信息可按原文保留在 content 中，也可省略，但不得改写；
   - 「待办 / 待办事项」区块可整段从 content 中删除（已单独放到 todos 字段），删除后不改其余；
   - 不做任何压缩/精简；仅当总长度超过 1800 字符时，从【尾部】截断多余部分，绝不改写或概括中间内容。
   一句话：content = 原文 − 无关噪声，除此之外原样不动。
4. attendees：从「参会人 / 参会人员」等字样后的 @人名 中提取姓名，去掉 @ 符号；
   必须排除混入的说明性文字（如「智能会议纪要由 AI 生成，可能不准确，请谨慎甄别后使用」
   不是人名）。只保留真实人名，去重。原文没有参会人时返回空数组 []。
5. todos：从「待办 / 待办事项 / 后续动作」等区块逐条提取：
   - text 为该待办的完整描述（可含背景与要求），去掉其中的 @人名 标记与「（来自X）」等来源批注，
     但来源批注里的信息若属于待办内容可保留语义；
   - assignees 为该条待办明确的责任人：取该条中出现的 @人名（去 @）；一条可有多个；
     无明确责任人时返回空数组 []；
   - 「（来自杨晶）」表示提出人而非责任人，不要据此把「杨晶」当责任人（除非同一条另有 @杨晶）。
   原文没有待办区块时返回空数组 []。
6. 所有人名只能来自 raw_text；若某人名与 known_users 中的某个昵称明显指向同一人，
   返回 known_users 中的那个昵称（规范化）；否则原样返回原文中的写法。禁止编造 known_users 里
   有、但 raw_text 未提及的人。
7. 语言使用简体中文，保持客观。整个 JSON 内容务必是合法 JSON（字符串内的换行用 \\n 转义）。
"""

_REPAIR_PROMPT = (
    "你上一次的输出不是合法 JSON 或不符合要求的结构。"
    "请重新只输出符合规定结构的 JSON 对象本身，不要任何其他文字：\n\n上次输出：\n{bad}"
)


def _clean_reply(text: str) -> str:
    cleaned = _THINK_RE.sub("", text or "")
    cleaned = _THINK_UNCLOSED_RE.sub("", cleaned)
    cleaned = cleaned.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:\w+)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _extract_json(text: str) -> dict[str, Any] | None:
    """从回复中提取首个平衡的 JSON 对象。"""
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except (json.JSONDecodeError, ValueError):
        pass
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    obj = json.loads(text[start:i + 1])
                    return obj if isinstance(obj, dict) else None
                except (json.JSONDecodeError, ValueError):
                    return None
    return None


def _as_text(value: Any, max_len: int) -> str:
    if value is None:
        return ""
    return str(value).strip()[:max_len]


def _clean_name(value: Any) -> str:
    return str(value or "").strip().lstrip("@").strip()[:_MAX_NAME_LEN]


def _clean_names(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in value:
        name = _clean_name(item)
        # 过滤明显的非人名噪声（免责声明整句混入等）
        if not name or len(name) > 20 or name in seen:
            continue
        seen.add(name)
        out.append(name)
    return out


def _sanitize(data: dict[str, Any], meet_types: dict[str, Any]) -> dict[str, Any]:
    """字段级清洗：结构强对齐前端会议表单契约，越界内容截断/丢弃。"""
    raw_type = _as_text(data.get("type"), _MAX_NAME_LEN)
    meet_type = raw_type if (meet_types and raw_type in meet_types) else ""

    content = _as_text(data.get("content"), _MAX_CONTENT)

    attendees = _clean_names(data.get("attendees"))[:_MAX_ATTENDEES]

    todos: list[dict[str, Any]] = []
    for row in (data.get("todos") or [])[:_MAX_TODOS]:
        if not isinstance(row, dict):
            continue
        text = _as_text(row.get("text"), _MAX_TODO_TEXT)
        if not text:
            continue
        todos.append({
            "text": text,
            "assignees": _clean_names(row.get("assignees"))[:_MAX_ATTENDEES],
        })

    return {
        "type": meet_type,
        "content": content,
        "attendees": attendees,
        "todos": todos,
    }


def _has_content(moment: dict[str, Any]) -> bool:
    return bool(moment.get("content") or moment.get("attendees") or moment.get("todos"))


def execute(slots: dict[str, Any]) -> dict[str, Any]:
    raw_text = str(slots.get("raw_text") or "").strip()
    meet_types = slots.get("meet_types") if isinstance(slots.get("meet_types"), dict) else {}
    known_users = slots.get("known_users") if isinstance(slots.get("known_users"), list) else []

    payload = json.dumps(
        {"raw_text": raw_text, "meet_types": meet_types, "known_users": known_users},
        ensure_ascii=False,
        default=str,
    )
    user_prompt = (
        "请根据以下会议纪要原文，抽取「会议动态」表单回填数据（只输出 JSON 对象）：\n\n"
        f"{payload}"
    )

    # 飞书同步不宜等全局 900s：超时后 51PM 会先报「AI 分析超时」，真实 401/格式错误出不来
    client = get_request_llm_client(timeout=90)
    raw = client.complete(SYSTEM_PROMPT, user_prompt)

    reply = _clean_reply(raw)
    parsed = _extract_json(reply)

    if parsed is None:
        raw = client.complete(SYSTEM_PROMPT, _REPAIR_PROMPT.format(bad=reply[:2000]))
        parsed = _extract_json(_clean_reply(raw))

    if parsed is None:
        raise AppError(code="llm_error", message="LLM did not return valid JSON", status_code=502)

    moment = _sanitize(parsed, meet_types)
    if not _has_content(moment):
        raise AppError(code="llm_error", message="LLM returned empty moment after sanitize", status_code=502)

    return {"moment": moment}
