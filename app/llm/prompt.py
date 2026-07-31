def build_system_prompt(intents_doc: str) -> str:
    return (
        "You route user messages to supported intents.\n"
        "Return only a JSON object with this exact shape: "
        '{"intent":"<intent name>","slots":{}}.\n'
        "Do not include Markdown fences or explanatory text.\n\n"
        "Supported intents:\n"
        f"{intents_doc.strip()}"
    )
