from __future__ import annotations

import asyncio
import logging

from telegram import Bot
from telegram.error import RetryAfter, TelegramError, TimedOut

from message_format import split_for_telegram
from version import telegram_version_banner

_SEND_ATTEMPTS = 4
_BASE_BACKOFF_SECONDS = 1.0


async def send_formatted_text(
    chat_id: str,
    text: str,
    *,
    bot: Bot,
    service_version: str,
    allowed_chat_ids: frozenset[int] | None = None,
) -> None:
    """Send full text, splitting into several Telegram messages if needed."""
    cid = int(chat_id)
    if allowed_chat_ids is not None and cid not in allowed_chat_ids:
        raise RuntimeError(f"Refusing to send: chat_id {cid} not in TELEGRAM_ALLOWED_CHAT_IDS")
    banner = telegram_version_banner(service_version)
    for chunk in split_for_telegram(text, leading_banner=banner):
        for attempt in range(1, _SEND_ATTEMPTS + 1):
            try:
                await bot.send_message(chat_id=cid, text=chunk)
                break
            except RetryAfter as exc:
                wait = max(float(exc.retry_after), _BASE_BACKOFF_SECONDS)
                logging.warning("Telegram RetryAfter for chat_id=%s; wait=%.1fs", cid, wait)
                await asyncio.sleep(wait)
            except (TimedOut, TelegramError):
                if attempt >= _SEND_ATTEMPTS:
                    raise
                wait = _BASE_BACKOFF_SECONDS * (2 ** (attempt - 1))
                logging.warning(
                    "Telegram send failed (attempt %s/%s), retry in %.1fs",
                    attempt,
                    _SEND_ATTEMPTS,
                    wait,
                    exc_info=True,
                )
                await asyncio.sleep(wait)
