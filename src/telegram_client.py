from __future__ import annotations

from telegram import Bot


def build_message(parsed: dict[str, str], snippet_limit: int = 500) -> str:
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
