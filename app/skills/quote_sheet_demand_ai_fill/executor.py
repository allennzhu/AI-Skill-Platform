from __future__ import annotations

import base64
import json
import re
from typing import Any

from app.api.errors import AppError
from app.llm.credentials import get_request_llm_client

_THINK_RE = re.compile(r"<think>[\s\S]*?</think>", re.IGNORECASE)
_THINK_UNCLOSED_RE = re.compile(r"<think>[\s\S]*$", re.IGNORECASE)

_MAX_NAME_LEN = 200
_MAX_DESC_LEN = 2000
_MAX_VERSION_LEN = 120
_MAX_PDF_PAGES = 4
_MAX_IMAGE_BYTES = 3_000_000
_MAX_DEMANDS = 30
_ALLOWED_MISSING_FIELDS = {
    "assigned_to",
    "start_date",
    "end_date",
    "standard_price",
    "standard_hour",
    "version",
    "demand_name",
    "amount",
    "unit",
}

SYSTEM_PROMPT = """你是「报价单 -> 51PM 初始需求草稿」的信息抽取助手。

用户会提供两类输入之一：
- 报价单 PDF 提取出的原始文本
- 扫描版报价单的页面图片

你的任务是把报价明细表里的每一条「内容」抽成一条 51PM 初始需求。

报价单通常分两部分：
- 头部：关联商机、关联客户、报价日期、价格政策 等元数据。这些不是需求。
- 明细表：列一般为「模块 / 内容 / 原价 / 折扣率 / 实际售价」。真正的需求是「内容」列的每一行。

输出必须是一个 JSON 对象，结构严格如下：
{
  "version": "4.1.0",
  "quote_demands": [
    {
      "demand_name": "CIM-CIM场景套餐-通用套餐-CIM高精度套餐（园区极致美）",
      "description": "模块：1. 场景之美 / 行业要素",
      "amount": 110,
      "unit": "万方",
      "assigned_to_name": "",
      "start_date": "",
      "end_date": "",
      "missing_fields": ["assigned_to", "start_date", "end_date"]
    }
  ]
}

硬性规则：
1. 只输出 JSON 对象本身，禁止 Markdown、代码块、解释文字。
2. 所有字段都必须来自原文，禁止编造。
3. quote_demands：明细表「内容」列有几条有效产品/服务条目，就输出几条。不要合并成一条。
4. demand_name：必须取「内容」列的产品路径/条目名称，用于后续 ECP 规则匹配。
   - 正确示例：CIM-CIM室内专项要素-城市园区室内结构还原-室内L2 (简易材质)
   - 禁止用：关联商机、项目标题、客户名、报价单文件名。
   - 禁止只用一级「模块」名，例如「1. 场景之美」「行业要素」「WDP API」。
   - 内容末尾的数量+单位不要写进 demand_name，放到 amount/unit。
5. description：可写所属模块名，以及该条内容原文；不要扩写。
6. amount：从该条「内容」末尾或数量列提取数量；无明确数量时返回 0。不要把原价/售价当作数量。
7. unit：该条数量对应单位，如 万方、m²、种、项；无则空串。
8. version：整个报价单共用，只能取头部「价格政策」字段的值；不要从标题「标准版」或文档编号猜。无则空串。
9. assigned_to_name、start_date、end_date：原文没有就返回空串，不得猜测。
10. missing_fields：只列出当前为空或不可确认的字段；只能从以下集合中选择：
    assigned_to, start_date, end_date, standard_price, standard_hour, version, demand_name, amount, unit
11. 日期统一输出 YYYY-MM-DD；无法标准化时返回空串。
12. 返回合法 JSON。
"""

_REPAIR_PROMPT = (
    "你上一次的输出不是合法 JSON 或结构不符合要求。"
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


def _as_amount(value: Any) -> float:
    if value is None or value == "":
        return 0
    try:
        amount = float(str(value).replace(",", "").strip())
    except ValueError:
        return 0
    if amount < 0:
        return 0
    return amount


def _sanitize_missing_fields(value: Any, sanitized: dict[str, Any]) -> list[str]:
    fields: list[str] = []
    if isinstance(value, list):
        for item in value:
            name = str(item or "").strip()
            if name in _ALLOWED_MISSING_FIELDS and name not in fields:
                fields.append(name)
    fallback_map = {
        "demand_name": sanitized["demand_name"] == "",
        "amount": sanitized["amount"] <= 0,
        "unit": sanitized["unit"] == "",
        "version": sanitized["version"] == "",
        "assigned_to": sanitized["assigned_to_name"] == "",
        "start_date": sanitized["start_date"] == "",
        "end_date": sanitized["end_date"] == "",
    }
    for key, missing in fallback_map.items():
        if missing and key not in fields:
            fields.append(key)
    return fields


def _sanitize(data: dict[str, Any]) -> dict[str, Any]:
    sanitized = {
        "demand_name": _as_text(data.get("demand_name"), _MAX_NAME_LEN),
        "description": _as_text(data.get("description"), _MAX_DESC_LEN),
        "amount": _as_amount(data.get("amount")),
        "unit": _as_text(data.get("unit"), 40),
        "version": _as_text(data.get("version"), _MAX_VERSION_LEN),
        "assigned_to_name": _as_text(data.get("assigned_to_name"), 40),
        "start_date": _as_text(data.get("start_date"), 20),
        "end_date": _as_text(data.get("end_date"), 20),
    }
    sanitized["missing_fields"] = _sanitize_missing_fields(data.get("missing_fields"), sanitized)
    return sanitized


def _has_content(data: dict[str, Any]) -> bool:
    return bool(data.get("demand_name") or data.get("description"))


def _pdf_to_image_parts(pdf_base64: str) -> list[dict[str, Any]]:
    try:
        import fitz
    except ModuleNotFoundError as exc:
        raise AppError(
            code="llm_error",
            message="当前环境缺少 PyMuPDF（fitz），暂时无法识别扫描版报价单",
            status_code=502,
        ) from exc

    try:
        raw = base64.b64decode(pdf_base64, validate=True)
    except (ValueError, TypeError) as exc:
        raise AppError(code="llm_error", message="扫描报价单文件解码失败", status_code=502) from exc

    try:
        doc = fitz.open(stream=raw, filetype="pdf")
    except Exception as exc:
        raise AppError(code="llm_error", message="扫描报价单 PDF 打开失败", status_code=502) from exc

    parts: list[dict[str, Any]] = []
    page_count = min(doc.page_count, _MAX_PDF_PAGES)
    for i in range(page_count):
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        png_bytes = pix.tobytes("png")
        if len(png_bytes) > _MAX_IMAGE_BYTES:
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
            png_bytes = pix.tobytes("png")
        data_url = "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")
        parts.append({"type": "image_url", "image_url": {"url": data_url}})
    if not parts:
        raise AppError(code="llm_error", message="扫描报价单未渲染出页面图片", status_code=502)
    return parts


def _looks_like_header_name(name: str) -> bool:
    text = (name or "").strip()
    if not text:
        return True
    header_keys = ("关联商机", "关联客户", "关联POC", "报价日期", "价格政策", "项目属性", "全量报价")
    if any(key in text for key in header_keys):
        return True
    if text.startswith("SJ") and "项目" in text:
        return True
    if "项目" in text and "-" not in text:
        return True
    return False


def _collect_demands(parsed: dict[str, Any], version: str) -> list[dict[str, Any]]:
    raw_items: list[Any] = []
    if isinstance(parsed.get("quote_demands"), list):
        raw_items = parsed["quote_demands"]
    elif isinstance(parsed.get("quote_demand"), dict):
        raw_items = [parsed["quote_demand"]]
    elif "demand_name" in parsed:
        raw_items = [parsed]

    demands: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        data = dict(item)
        if not str(data.get("version") or "").strip():
            data["version"] = version
        sanitized = _sanitize(data)
        name = sanitized["demand_name"]
        if not _has_content(sanitized) or _looks_like_header_name(name):
            continue
        if name in seen:
            continue
        seen.add(name)
        demands.append(sanitized)
        if len(demands) >= _MAX_DEMANDS:
            break
    return demands


def execute(slots: dict[str, Any]) -> dict[str, Any]:
    raw_text = str(slots.get("raw_text") or "").strip()
    pdf_base64 = str(slots.get("pdf_base64") or "").strip()
    file_name = str(slots.get("file_name") or "").strip()
    timeout = 180 if pdf_base64 and not raw_text else 90
    client = get_request_llm_client(timeout=timeout)

    if raw_text:
        payload = json.dumps({"raw_text": raw_text}, ensure_ascii=False, default=str)
        user_content: str | list[dict[str, Any]] = (
            "请根据以下报价单原文，按明细表「内容」列逐条抽取 51PM 初始需求（只输出 JSON 对象）。"
            "不要把关联商机/项目标题当成需求名称。\n\n"
            f"{payload}"
        )
    elif pdf_base64:
        intro = (
            "请识别这些扫描版报价单页面图片，按明细表「内容」列逐条抽取 51PM 初始需求，只输出 JSON 对象。"
            "不要把关联商机/项目标题当成需求名称。"
        )
        if file_name:
            intro += f"\n文件名：{file_name}"
        intro += "\n重点：version 只取头部“价格政策”；demand_name 只取「内容」列。"
        user_content = [{"type": "text", "text": intro}]
        user_content.extend(_pdf_to_image_parts(pdf_base64))
    else:
        raise AppError(code="llm_error", message="缺少报价单文本或扫描 PDF", status_code=502)

    raw = client.complete(SYSTEM_PROMPT, user_content)
    reply = _clean_reply(raw)
    parsed = _extract_json(reply)
    if parsed is None:
        raw = client.complete(SYSTEM_PROMPT, _REPAIR_PROMPT.format(bad=reply[:2000]))
        parsed = _extract_json(_clean_reply(raw))
    if parsed is None:
        raise AppError(code="llm_error", message="LLM did not return valid JSON quote demand", status_code=502)

    version = _as_text(parsed.get("version"), _MAX_VERSION_LEN)
    quote_demands = _collect_demands(parsed, version)
    if not quote_demands:
        raise AppError(code="llm_error", message="LLM returned empty quote demand after sanitize", status_code=502)
    return {"version": version, "quote_demands": quote_demands}
