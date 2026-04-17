"""
Plain-text email → Telegram message body. Swap or extend here for Markdown/HTML later.
"""

from __future__ import annotations

from typing import List

# Telegram hard limit for sendMessage text
TELEGRAM_MAX_MESSAGE_LENGTH = 4096
# Conservative body limit to stay under UTF-16 unit limits for emoji-heavy text.
TELEGRAM_SAFE_MESSAGE_LENGTH = 3500
# Reserve for "(part i/n)\n" line
_PART_OVERHEAD = 32


def format_email_plain(parsed: dict[str, str]) -> str:
    body = (parsed.get("body") or "").replace("\r\n", "\n").strip() or "(empty body)"
    return (
        "📧 Новое письмо\n"
        f"От: {parsed.get('from', '')}\n"
        f"Тема: {parsed.get('subject', '')}\n"
        f"Дата: {parsed.get('date', '')}\n"
        f"\n{body}"
    )


def split_for_telegram(text: str, *, leading_banner: str = "") -> List[str]:
    """Split into chunks that fit Telegram after optional banner and part prefix."""
    banner_prefix = (leading_banner + "\n") if leading_banner else ""
    overhead = _PART_OVERHEAD + len(banner_prefix)
    max_body_per_message = TELEGRAM_SAFE_MESSAGE_LENGTH - overhead
    if max_body_per_message <= 0:
        raise ValueError("leading_banner is too long for Telegram message limit")

    if len(banner_prefix) + len(text) <= TELEGRAM_SAFE_MESSAGE_LENGTH:
        return [banner_prefix + text] if banner_prefix else [text]

    raw_chunks: List[str] = []
    pos = 0
    while pos < len(text):
        raw_chunks.append(text[pos : pos + max_body_per_message])
        pos += max_body_per_message
    n = len(raw_chunks)
    return [f"{banner_prefix}({i + 1}/{n})\n{chunk}" for i, chunk in enumerate(raw_chunks)]
