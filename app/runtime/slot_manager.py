class SlotManager:
    def missing(self, required: list[str], slots: dict) -> list[str]:
        out = []
        for name in required:
            if name not in slots or slots[name] is None or slots[name] == "":
                out.append(name)
        return out
