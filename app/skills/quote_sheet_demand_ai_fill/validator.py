from typing import Any


def validate(slots: dict[str, Any]) -> None:
    raw_text = slots.get("raw_text")
    pdf_base64 = slots.get("pdf_base64")
    has_raw_text = isinstance(raw_text, str) and bool(raw_text.strip())
    has_pdf = isinstance(pdf_base64, str) and bool(pdf_base64.strip())

    if not has_raw_text and not has_pdf:
        raise ValueError("raw_text or pdf_base64 required")
    if has_raw_text and len(raw_text.strip()) < 10:
        raise ValueError("raw_text too short to analyze")
