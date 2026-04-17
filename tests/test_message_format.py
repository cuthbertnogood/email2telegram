from __future__ import annotations

from message_format import TELEGRAM_SAFE_MESSAGE_LENGTH, split_for_telegram


def test_split_for_telegram_single_chunk() -> None:
    chunks = split_for_telegram("hello", leading_banner="[email2telegram v1]")
    assert len(chunks) == 1
    assert chunks[0].startswith("[email2telegram v1]")


def test_split_for_telegram_multiple_chunks() -> None:
    text = "x" * (TELEGRAM_SAFE_MESSAGE_LENGTH * 2)
    chunks = split_for_telegram(text, leading_banner="[banner]")
    assert len(chunks) >= 2
    assert chunks[0].startswith("[banner]\n(1/")
