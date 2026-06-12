from __future__ import annotations

import pytest

from pipeline import run_delivery_cycle


class DummyClient:
    def __init__(self, messages):
        self._messages = messages
        self.marked: list[int] = []
        self.last_unseen_only: bool | None = None

    def fetch_new_messages(
        self,
        last_seen_uid,
        *,
        unseen_only: bool = False,
        max_messages: int | None = None,
    ):
        self.last_unseen_only = unseen_only
        messages = list(self._messages)
        if max_messages is not None:
            messages = messages[:max_messages]
        return messages

    def mark_uids_seen(self, uids):
        self.marked.extend(uids)


class DummyState:
    def __init__(self, last_seen_uid=None):
        self.last_seen_uid = last_seen_uid
        self.ids = set()
        self.last_seen_history: list[int] = []

    def get_last_seen_uid(self):
        return self.last_seen_uid

    def set_last_seen_uid(self, uid):
        self.last_seen_uid = uid
        self.last_seen_history.append(uid)

    def has_message_id(self, message_id):
        return message_id in self.ids

    def add_message_id(self, message_id):
        self.ids.add(message_id)


class DummyBot:
    async def send_message(self, chat_id, text):
        return None


def _raw(uid: int) -> bytes:
    return (
        f"From: sender@example.com\r\n"
        f"Subject: Test {uid}\r\n"
        f"Date: Fri, 17 Apr 2026 12:00:00 +0000\r\n"
        f"Message-ID: <uid-{uid}@example.com>\r\n"
        f"\r\n"
        f"body {uid}\r\n"
    ).encode()


@pytest.mark.asyncio
async def test_run_delivery_cycle_happy_path(monkeypatch) -> None:
    client = DummyClient([(10, _raw(10))])
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
        service_version="0.17.7",
        allowed_chat_ids=frozenset({123}),
        max_messages_per_poll=50,
        imap_unseen_only=True,
    )
    assert state.last_seen_uid == 10
    assert state.last_seen_history == [10]
    assert client.marked == [10]
    assert client.last_unseen_only is True


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
        service_version="0.17.7",
        allowed_chat_ids=frozenset({123}),
    )
    assert state.last_seen_uid == 3
    assert client.marked == []


@pytest.mark.asyncio
async def test_run_delivery_cycle_max_per_poll(monkeypatch) -> None:
    messages = [(i, _raw(i)) for i in range(1, 6)]
    client = DummyClient(messages)
    state = DummyState(last_seen_uid=None)

    async def fake_send_formatted_text(**kwargs):
        return None

    monkeypatch.setattr("pipeline.send_formatted_text", fake_send_formatted_text)
    await run_delivery_cycle(
        client,
        state,
        chat_id="123",
        bot=DummyBot(),
        export_dir=None,
        service_version="0.17.7",
        allowed_chat_ids=frozenset({123}),
        max_messages_per_poll=2,
    )
    assert state.last_seen_uid == 2
    assert state.last_seen_history == [1, 2]
    assert client.marked == [1, 2]


@pytest.mark.asyncio
async def test_run_delivery_cycle_dedup_skip_advances_cursor(monkeypatch) -> None:
    client = DummyClient([(11, _raw(11))])
    state = DummyState(last_seen_uid=10)
    state.ids.add("mid:uid-11@example.com")

    async def fake_send_formatted_text(**kwargs):
        raise AssertionError("dedup skip should not send")

    monkeypatch.setattr("pipeline.send_formatted_text", fake_send_formatted_text)
    await run_delivery_cycle(
        client,
        state,
        chat_id="123",
        bot=DummyBot(),
        export_dir=None,
        service_version="0.17.7",
        allowed_chat_ids=frozenset({123}),
    )
    assert state.last_seen_uid == 11
    assert client.marked == [11]


@pytest.mark.asyncio
async def test_run_delivery_cycle_checkpoint_on_delivery_failure(monkeypatch) -> None:
    client = DummyClient([(20, _raw(20)), (21, _raw(21))])
    state = DummyState(last_seen_uid=19)
    calls = {"n": 0}

    async def fake_send_formatted_text(**kwargs):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("telegram down")
        return None

    monkeypatch.setattr("pipeline.send_formatted_text", fake_send_formatted_text)
    await run_delivery_cycle(
        client,
        state,
        chat_id="123",
        bot=DummyBot(),
        export_dir=None,
        service_version="0.17.7",
        allowed_chat_ids=frozenset({123}),
    )
    assert state.last_seen_uid == 20
    assert client.marked == [20]
