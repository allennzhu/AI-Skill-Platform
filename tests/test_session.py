import time
from app.runtime.session import SessionStore


def test_create_and_merge_slots():
    store = SessionStore(ttl_seconds=60)
    s = store.create()
    assert s.session_id
    s = store.merge_slots(s, intent="echo", slots={"text": "a"})
    s = store.merge_slots(s, intent="echo", slots={"text": "b", "extra": 1})
    assert s.slots == {"text": "b", "extra": 1}
    assert s.intent == "echo"
    store.save(s)
    loaded = store.get(s.session_id)
    assert loaded is not None
    assert loaded.slots["text"] == "b"


def test_expired_session_returns_none():
    store = SessionStore(ttl_seconds=1)
    s = store.create()
    store.save(s)
    s.updated_at = time.time() - 10
    store.save(s)
    assert store.get(s.session_id) is None
