from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

from dotenv import load_dotenv

from imap_client import ImapClient
from parser import parse_email
from state import StateStore
from telegram_client import build_message, send_message


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


async def run_once(client: ImapClient, state: StateStore, bot_token: str, chat_id: str) -> Optional[int]:
    last_seen = state.get_last_seen_uid()
    messages = client.fetch_new_messages(last_seen_uid=last_seen)
    if not messages:
        return last_seen

    newest_uid = last_seen
    for uid, raw in messages:
        parsed = parse_email(raw)
        text = build_message(parsed)
        await send_message(bot_token=bot_token, chat_id=chat_id, text=text)
        newest_uid = uid if newest_uid is None else max(newest_uid, uid)

    if newest_uid is not None:
        state.set_last_seen_uid(newest_uid)
    return newest_uid


async def main() -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    imap_host = _required_env("IMAP_HOST")
    imap_port = int(os.getenv("IMAP_PORT", "993"))
    imap_user = _required_env("IMAP_USER")
    imap_pass = _required_env("IMAP_PASS")
    imap_mailbox = os.getenv("IMAP_MAILBOX", "INBOX")
    poll_interval = int(os.getenv("POLL_INTERVAL_SECONDS", "45"))

    bot_token = _required_env("TELEGRAM_BOT_TOKEN")
    chat_id = _required_env("TELEGRAM_CHAT_ID")

    imap_client = ImapClient(
        host=imap_host,
        port=imap_port,
        user=imap_user,
        password=imap_pass,
        mailbox=imap_mailbox,
    )
    state = StateStore()

    logging.info("email2telegram started. Poll interval: %ss", poll_interval)
    while True:
        try:
            await run_once(imap_client, state, bot_token, chat_id)
        except Exception as exc:
            logging.exception("polling cycle failed: %s", exc)
        await asyncio.sleep(poll_interval)


if __name__ == "__main__":
    asyncio.run(main())
