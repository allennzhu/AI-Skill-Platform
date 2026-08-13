from __future__ import annotations

from typing import Any

# 会议纪要原文可能较长（智能纪要动辄数千字），预算放宽到 16000 字符；
# 超出时截断尾部（正文核心结论通常在前中段，「相关链接/文字记录」等尾部为噪声）。
_MAX_RAW_CHARS = 16000
_MAX_MEET_TYPES = 40
_MAX_KNOWN_USERS = 400
_MAX_NAME_LEN = 40


def _clean_name(value: Any) -> str:
    return str(value or "").strip().lstrip("@").strip()[:_MAX_NAME_LEN]


def normalize(slots: dict[str, Any]) -> dict[str, Any]:
    raw_text = str(slots.get("raw_text") or "").strip()
    if len(raw_text) > _MAX_RAW_CHARS:
        raw_text = raw_text[:_MAX_RAW_CHARS]

    out: dict[str, Any] = {"raw_text": raw_text}

    meet_types = slots.get("meet_types")
    if isinstance(meet_types, dict) and meet_types:
        trimmed: dict[str, str] = {}
        for key, label in list(meet_types.items())[:_MAX_MEET_TYPES]:
            k = str(key).strip()
            if k:
                trimmed[k] = str(label).strip()[:_MAX_NAME_LEN]
        if trimmed:
            out["meet_types"] = trimmed

    known_users = slots.get("known_users")
    if isinstance(known_users, list) and known_users:
        names: list[str] = []
        seen: set[str] = set()
        for name in known_users:
            n = _clean_name(name)
            if n and n not in seen:
                seen.add(n)
                names.append(n)
            if len(names) >= _MAX_KNOWN_USERS:
                break
        if names:
            out["known_users"] = names

    return out
