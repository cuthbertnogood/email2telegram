from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from imap_client import ImapClient
from message_format import format_email_plain
from parser import parse_email
from state import StateStore
from telegram_client import send_formatted_text


def _write_eml(export_dir: Path, uid: int, raw: bytes) -> None:
    export_dir.mkdir(parents=True, exist_ok=True)
    (export_dir / f"{uid}.eml").write_bytes(raw)


async def run_delivery_cycle(
    client: ImapClient,
    state: StateStore,
    bot_token: str,
    chat_id: str,
    export_dir: Optional[Path],
    *,
    allowed_chat_ids: frozenset[int] | None = None,
) -> None:
    last_seen = state.get_last_seen_uid()
    messages = await asyncio.to_thread(client.fetch_new_messages, last_seen)
    if not messages:
        logging.info("no new messages (last_seen_uid=%s)", last_seen)
        return

    messages = sorted(messages, key=lambda x: x[0])
    processed: list[int] = []

    for uid, raw in messages:
        try:
            if export_dir is not None:
                await asyncio.to_thread(_write_eml, export_dir, uid, raw)
            parsed = parse_email(raw)
            formatted = format_email_plain(parsed)
            await send_formatted_text(
                bot_token=bot_token,
                chat_id=chat_id,
                text=formatted,
                allowed_chat_ids=allowed_chat_ids,
            )
            processed.append(uid)
            logging.info("delivered UID %s to Telegram", uid)
        except Exception:
            logging.exception("delivery failed for uid=%s; stopping batch", uid)
            break

    if not processed:
        return

    await asyncio.to_thread(client.mark_uids_seen, processed)

    def _persist_state() -> None:
        state.set_last_seen_uid(max(processed))

    await asyncio.to_thread(_persist_state)


def load_export_dir_from_env() -> Optional[Path]:
    load_dotenv()
    raw = os.getenv("EXPORT_MAIL_DIR", "").strip()
    if not raw:
        return None
    return Path(raw)
