from app.runtime.slot_manager import SlotManager


def test_missing_slots_ordered():
    m = SlotManager()
    assert m.missing(["text", "date"], {}) == ["text", "date"]
    assert m.missing(["text", "date"], {"text": "x"}) == ["date"]
    assert m.missing(["text"], {"text": "x"}) == []
