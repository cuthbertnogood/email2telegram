from __future__ import annotations

from state import StateStore


def test_state_store_last_seen_uid_roundtrip(tmp_path) -> None:
    state_path = tmp_path / ".state.json"
    store = StateStore(path=str(state_path))
    assert store.get_last_seen_uid() is None
    store.set_last_seen_uid(42)
    assert store.get_last_seen_uid() == 42


def test_state_store_message_id_dedup(tmp_path) -> None:
    store = StateStore(path=str(tmp_path / ".state.json"))
    assert not store.has_message_id("mid:1")
    store.add_message_id("mid:1")
    assert store.has_message_id("mid:1")
