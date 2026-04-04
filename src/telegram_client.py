from __future__ import annotations

from telegram import Bot

from message_format import split_for_telegram


def build_message(parsed: dict[str, str], snippet_limit: int = 500) -> str:
    """Short preview (used by imap_probe-style tooling if needed)."""
    body = (parsed.get("body") or "").replace("\r\n", "\n").strip()
    snippet = body[:snippet_limit] if body else "(empty body)"
    return (
        f"New email\n"
        f"From: {parsed.get('from', '')}\n"
        f"Subject: {parsed.get('subject', '')}\n"
        f"Date: {parsed.get('date', '')}\n\n"
        f"{snippet}"
    )


async def send_message(bot_token: str, chat_id: str, text: str) -> None:
    bot = Bot(token=bot_token)
    await bot.send_message(chat_id=chat_id, text=text)


async def send_formatted_text(
    bot_token: str,
    chat_id: str,
    text: str,
    *,
    allowed_chat_ids: frozenset[int] | None = None,
) -> None:
    """Send full text, splitting into several Telegram messages if needed."""
    cid = int(chat_id)
    if allowed_chat_ids is not None and cid not in allowed_chat_ids:
        raise RuntimeError(f"Refusing to send: chat_id {cid} not in TELEGRAM_ALLOWED_CHAT_IDS")
    bot = Bot(token=bot_token)
    for chunk in split_for_telegram(text):
        await bot.send_message(chat_id=cid, text=chunk)
