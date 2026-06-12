from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from telegram import Bot

from imap_client import ImapClient
from message_format import format_email_plain
from parser import parse_email
from state import StateStore
from telegram_client import send_formatted_text

_SEEN_FLUSH_BATCH = 10


def _write_eml(export_dir: Path, uid: int, raw: bytes) -> None:
    export_dir.mkdir(parents=True, exist_ok=True)
    (export_dir / f"{uid}.eml").write_bytes(raw)


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name, "").strip().lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on")


def load_max_messages_per_poll() -> int:
    load_dotenv()
    value = _env_int("E2T_MAX_MESSAGES_PER_POLL", 50)
    return max(1, value)


def load_imap_unseen_only() -> bool:
    load_dotenv()
    return _env_bool("E2T_IMAP_UNSEEN_ONLY", True)


async def _checkpoint_uid(
    client: ImapClient,
    state: StateStore,
    uid: int,
    pending_seen: list[int],
) -> None:
    await asyncio.to_thread(state.set_last_seen_uid, uid)
    pending_seen.append(uid)
    if len(pending_seen) >= _SEEN_FLUSH_BATCH:
        batch = list(pending_seen)
        pending_seen.clear()
        try:
            await asyncio.to_thread(client.mark_uids_seen, batch)
        except Exception:
            logging.warning(
                "mark_uids_seen failed for uids=%s; last_seen_uid=%s already saved",
                batch,
                uid,
                exc_info=True,
            )


async def _flush_pending_seen(client: ImapClient, pending_seen: list[int]) -> None:
    if not pending_seen:
        return
    batch = list(pending_seen)
    pending_seen.clear()
    try:
        await asyncio.to_thread(client.mark_uids_seen, batch)
    except Exception:
        logging.warning(
            "mark_uids_seen failed for uids=%s at end of batch",
            batch,
            exc_info=True,
        )


async def run_delivery_cycle(
    client: ImapClient,
    state: StateStore,
    chat_id: str,
    bot: Bot,
    export_dir: Optional[Path],
    *,
    service_version: str,
    allowed_chat_ids: frozenset[int] | None = None,
    max_messages_per_poll: int = 50,
    imap_unseen_only: bool = True,
) -> None:
    last_seen = state.get_last_seen_uid()
    messages = await asyncio.to_thread(
        client.fetch_new_messages,
        last_seen,
        unseen_only=imap_unseen_only,
        max_messages=max_messages_per_poll,
    )
    _raw_uids = [u for u, _ in messages]
    if last_seen is not None:
        _stale = [u for u in _raw_uids if u <= last_seen]
        if _stale:
            logging.warning(
                "IMAP returned UID(s) <= last_seen_uid=%s; dropping %s (duplicate delivery guard)",
                last_seen,
                _stale,
            )
        messages = [(u, r) for u, r in messages if u > last_seen]
    if not messages:
        logging.debug(
            "no new messages (last_seen_uid=%s unseen_only=%s)",
            last_seen,
            imap_unseen_only,
        )
        return

    messages = sorted(messages, key=lambda x: x[0])

    logging.info(
        "poll: last_seen_uid=%s unseen_only=%s uids=%s",
        last_seen,
        imap_unseen_only,
        [u for u, _ in messages],
    )

    pending_seen: list[int] = []

    for uid, raw in messages:
        try:
            if export_dir is not None:
                await asyncio.to_thread(_write_eml, export_dir, uid, raw)
            parsed = parse_email(raw)
            dkey = (parsed.get("dedup_key") or "").strip()
            if dkey and await asyncio.to_thread(state.has_message_id, dkey):
                logging.info(
                    "skip UID %s: duplicate delivery key already sent (duplicate guard)",
                    uid,
                )
                await _checkpoint_uid(client, state, uid, pending_seen)
                continue
            formatted = format_email_plain(parsed)
            await send_formatted_text(
                chat_id=chat_id,
                text=formatted,
                bot=bot,
                service_version=service_version,
                allowed_chat_ids=allowed_chat_ids,
            )
            logging.info("delivered UID %s to Telegram", uid)
            if dkey:
                try:
                    await asyncio.to_thread(state.add_message_id, dkey)
                except Exception:
                    logging.exception(
                        "add_message_id failed for uid=%s; cursor still advances",
                        uid,
                    )
            await _checkpoint_uid(client, state, uid, pending_seen)
        except Exception:
            logging.exception("delivery failed for uid=%s; stopping batch", uid)
            break

    await _flush_pending_seen(client, pending_seen)


def load_export_dir_from_env() -> Optional[Path]:
    load_dotenv()
    raw = os.getenv("E2T_EXPORT_MAIL_DIR", "").strip()
    if not raw:
        return None
    return Path(raw)
