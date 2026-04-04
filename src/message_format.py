"""
Plain-text email → Telegram message body. Swap or extend here for Markdown/HTML later.
"""

from __future__ import annotations

from typing import List

# Telegram hard limit for sendMessage text
TELEGRAM_MAX_MESSAGE_LENGTH = 4096
# Reserve for "(part i/n)\n" line
_PART_OVERHEAD = 32
_CHUNK = TELEGRAM_MAX_MESSAGE_LENGTH - _PART_OVERHEAD


def format_email_plain(parsed: dict[str, str]) -> str:
    body = (parsed.get("body") or "").replace("\r\n", "\n").strip() or "(empty body)"
    return (
        "📧 Новое письмо\n"
        f"От: {parsed.get('from', '')}\n"
        f"Тема: {parsed.get('subject', '')}\n"
        f"Дата: {parsed.get('date', '')}\n"
        f"\n{body}"
    )


def split_for_telegram(text: str) -> List[str]:
    """Split into chunks that fit Telegram after optional part prefix."""
    if len(text) <= TELEGRAM_MAX_MESSAGE_LENGTH:
        return [text]
    raw_chunks: List[str] = []
    pos = 0
    while pos < len(text):
        raw_chunks.append(text[pos : pos + _CHUNK])
        pos += _CHUNK
    n = len(raw_chunks)
    if n <= 1:
        return raw_chunks
    return [f"({i + 1}/{n})\n{chunk}" for i, chunk in enumerate(raw_chunks)]
