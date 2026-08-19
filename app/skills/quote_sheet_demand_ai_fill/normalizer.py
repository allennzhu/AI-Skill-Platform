from __future__ import annotations

from typing import Any

_MAX_RAW_CHARS = 16000
_MAX_BASE64_CHARS = 8_000_000


def normalize(slots: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}

    raw_text = str(slots.get("raw_text") or "").strip()
    if raw_text:
        if len(raw_text) > _MAX_RAW_CHARS:
            raw_text = raw_text[:_MAX_RAW_CHARS]
        out["raw_text"] = raw_text

    pdf_base64 = str(slots.get("pdf_base64") or "").strip()
    if pdf_base64:
        out["pdf_base64"] = pdf_base64[:_MAX_BASE64_CHARS]

    file_name = str(slots.get("file_name") or "").strip()
    if file_name:
        out["file_name"] = file_name[:255]

    return out
