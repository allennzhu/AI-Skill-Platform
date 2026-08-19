class SlotManager:
    def missing(self, required: list[str], slots: dict) -> list[str]:
        out = []
        for name in required:
            value = slots.get(name) if name in slots else None
            if (
                name not in slots
                or value is None
                or value == ""
                or value == []
                or value == {}
            ):
                out.append(name)
        return out
