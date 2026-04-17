from __future__ import annotations

import pytest

from pipeline import run_delivery_cycle


class DummyClient:
    def __init__(self, messages):
        self._messages = messages
        self.marked = []

    def fetch_new_messages(self, last_seen_uid):
        return list(self._messages)

    def mark_uids_seen(self, uids):
        self.marked = list(uids)


class DummyState:
    def __init__(self, last_seen_uid=None):
        self.last_seen_uid = last_seen_uid
        self.ids = set()

    def get_last_seen_uid(self):
        return self.last_seen_uid

    def set_last_seen_uid(self, uid):
        self.last_seen_uid = uid

    def has_message_id(self, message_id):
        return message_id in self.ids

    def add_message_id(self, message_id):
        self.ids.add(message_id)


class DummyBot:
    async def send_message(self, chat_id, text):
        return None


@pytest.mark.asyncio
async def test_run_delivery_cycle_happy_path(monkeypatch) -> None:
    raw = (
        b"From: sender@example.com\r\n"
        b"Subject: Test\r\n"
        b"Date: Fri, 17 Apr 2026 12:00:00 +0000\r\n"
        b"Message-ID: <uid-1@example.com>\r\n"
        b"\r\n"
        b"body\r\n"
    )
    client = DummyClient([(10, raw)])
    state = DummyState(last_seen_uid=9)

    async def fake_send_formatted_text(**kwargs):
        return None

    monkeypatch.setattr("pipeline.send_formatted_text", fake_send_formatted_text)
    await run_delivery_cycle(
        client,
        state,
        chat_id="123",
        bot=DummyBot(),
        export_dir=None,
        service_version="0.8.2",
        allowed_chat_ids=frozenset({123}),
    )
    assert state.last_seen_uid == 10
    assert client.marked == [10]


@pytest.mark.asyncio
async def test_run_delivery_cycle_no_messages(monkeypatch) -> None:
    client = DummyClient([])
    state = DummyState(last_seen_uid=3)

    async def fake_send_formatted_text(**kwargs):
        raise AssertionError("should not send when no messages")

    monkeypatch.setattr("pipeline.send_formatted_text", fake_send_formatted_text)
    await run_delivery_cycle(
        client,
        state,
        chat_id="123",
        bot=DummyBot(),
        export_dir=None,
        service_version="0.8.2",
        allowed_chat_ids=frozenset({123}),
    )
    assert state.last_seen_uid == 3
