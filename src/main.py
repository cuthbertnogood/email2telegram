from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import logging
import os
import platform
import socket

from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, ContextTypes, filters

from allowlist import parse_allowed_chat_ids
from imap_client import ImapClient
from pipeline import load_export_dir_from_env, run_delivery_cycle
from state import StateStore
from telegram_client import send_formatted_text
from version import get_version


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _state_path() -> str:
    return os.getenv("STATE_FILE", ".state.json")


async def _poll_imap(context: ContextTypes.DEFAULT_TYPE) -> None:
    bd = context.application.bot_data
    try:
        await run_delivery_cycle(
            bd["imap_client"],
            bd["state"],
            chat_id=bd["chat_id"],
            bot=context.application.bot,
            export_dir=bd["export_dir"],
            service_version=bd["service_version"],
            allowed_chat_ids=bd["allowed_chat_ids"],
        )
    except Exception:
        logging.exception("IMAP delivery cycle failed")


async def _job_heartbeat(context: ContextTypes.DEFAULT_TYPE) -> None:
    bd = context.application.bot_data
    state = bd["state"]
    try:
        current = await asyncio.to_thread(state.get_heartbeat_counter)
        await send_formatted_text(
            bd["chat_id"],
            str(current),
            bot=context.application.bot,
            service_version=bd["service_version"],
            allowed_chat_ids=bd["allowed_chat_ids"],
        )
        await asyncio.to_thread(state.set_heartbeat_counter, current + 1)
    except Exception:
        logging.exception("Heartbeat job failed")


async def _cmd_start(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        ver = context.application.bot_data["service_version"]
        await update.message.reply_text(
            f"email2telegram v{ver}: почта доставляется в этот чат."
        )


def _build_startup_message(
    *,
    previous_version: str | None,
    current_version: str,
    startup_iso: str,
    hostname: str,
    python_version: str,
    app_version: str,
    poll_interval: float,
    state_path: str,
    export_dir: str,
) -> str:
    if previous_version is None:
        version_line = f"Версия: первый запуск на этом томе -> v{current_version}"
    else:
        version_line = f"Версия: v{previous_version} -> v{current_version}"
    return "\n".join(
        [
            "Обновление образа",
            version_line,
            f"Время: {startup_iso}",
            f"Host: {hostname}",
            f"Python: {python_version}",
            f"APP_VERSION (OCI label): {app_version or '-'}",
            f"Poll: {poll_interval}s",
            f"State: {state_path}",
            f"Export: {export_dir}",
        ]
    )


async def _notify_startup(application: Application) -> None:
    bd = application.bot_data
    state = bd["state"]
    current_version = bd["service_version"]
    previous_version = await asyncio.to_thread(state.get_last_service_version)
    if previous_version == current_version:
        return

    message = _build_startup_message(
        previous_version=previous_version,
        current_version=current_version,
        startup_iso=bd["startup_iso"],
        hostname=bd["hostname"],
        python_version=bd["python_version"],
        app_version=bd["app_version"],
        poll_interval=bd["poll_interval"],
        state_path=bd["state_path"],
        export_dir=bd["export_dir_text"],
    )
    try:
        await send_formatted_text(
            bd["chat_id"],
            message,
            bot=application.bot,
            service_version=current_version,
            allowed_chat_ids=bd["allowed_chat_ids"],
        )
        await asyncio.to_thread(state.set_last_service_version, current_version)
        logging.info("Startup update notice sent: %s -> %s", previous_version, current_version)
    except Exception:
        logging.exception("Failed to send startup update notice")


def main() -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    imap_host = _required_env("IMAP_HOST")
    imap_port = int(os.getenv("IMAP_PORT", "993"))
    imap_user = _required_env("IMAP_USER")
    imap_pass = _required_env("IMAP_PASS")
    imap_mailbox = os.getenv("IMAP_MAILBOX", "INBOX")
    poll_interval = float(os.getenv("POLL_INTERVAL_SECONDS", "45"))

    heartbeat_interval = float(os.getenv("HEARTBEAT_INTERVAL_SECONDS", "86400"))
    heartbeat_hour_raw = os.getenv("HEARTBEAT_HOUR", "9")
    heartbeat_minute_raw = os.getenv("HEARTBEAT_MINUTE", "0")
    try:
        heartbeat_hour = int(heartbeat_hour_raw, 10)
    except ValueError as exc:
        raise RuntimeError("HEARTBEAT_HOUR must be an integer 0-23") from exc
    if not 0 <= heartbeat_hour <= 23:
        raise RuntimeError("HEARTBEAT_HOUR must be between 0 and 23 inclusive")
    try:
        heartbeat_minute = int(heartbeat_minute_raw, 10)
    except ValueError as exc:
        raise RuntimeError("HEARTBEAT_MINUTE must be an integer 0-59") from exc
    if not 0 <= heartbeat_minute <= 59:
        raise RuntimeError("HEARTBEAT_MINUTE must be between 0 and 59 inclusive")

    bot_token = _required_env("TELEGRAM_BOT_TOKEN")
    chat_id = _required_env("TELEGRAM_CHAT_ID")
    allowed = parse_allowed_chat_ids(_required_env("TELEGRAM_ALLOWED_CHAT_IDS"))

    chat_id_int = int(chat_id)
    if chat_id_int not in allowed:
        raise RuntimeError("TELEGRAM_CHAT_ID must be included in TELEGRAM_ALLOWED_CHAT_IDS")

    export_dir = load_export_dir_from_env()
    state_path = _state_path()
    startup_iso = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    hostname = socket.gethostname()
    python_version = platform.python_version()
    app_version = os.getenv("APP_VERSION", "").strip()
    export_dir_text = str(export_dir.resolve()) if export_dir else "-"

    imap_client = ImapClient(
        host=imap_host,
        port=imap_port,
        user=imap_user,
        password=imap_pass,
        mailbox=imap_mailbox,
    )
    state = StateStore(path=state_path)
    service_version = get_version()

    application = Application.builder().token(bot_token).post_init(_notify_startup).build()

    application.bot_data.update(
        {
            "imap_client": imap_client,
            "state": state,
            "chat_id": chat_id,
            "export_dir": export_dir,
            "allowed_chat_ids": allowed,
            "service_version": service_version,
            "poll_interval": poll_interval,
            "state_path": state_path,
            "startup_iso": startup_iso,
            "hostname": hostname,
            "python_version": python_version,
            "app_version": app_version,
            "export_dir_text": export_dir_text,
        }
    )

    chat_filter = filters.Chat(chat_id=list(allowed))
    application.add_handler(CommandHandler("start", _cmd_start, filters=chat_filter))

    jq = application.job_queue
    if jq is None:
        raise RuntimeError("JobQueue unavailable; pip install 'python-telegram-bot[job-queue]'")
    jq.run_repeating(_poll_imap, interval=poll_interval, first=5.0)

    if heartbeat_interval > 0:
        now_local = datetime.now(timezone.utc).astimezone()
        hi = heartbeat_interval
        hi_i = int(hi)
        if hi_i != hi:
            raise RuntimeError("HEARTBEAT_INTERVAL_SECONDS must be a whole number of seconds")
        if hi_i >= 86400:
            if hi_i % 86400 != 0:
                raise RuntimeError(
                    "HEARTBEAT_INTERVAL_SECONDS >= 86400 must be a multiple of 86400 (whole days)"
                )
            # Once (or every N days): next local wall time HEARTBEAT_HOUR:HEARTBEAT_MINUTE, then fixed interval.
            target = now_local.replace(
                hour=heartbeat_hour, minute=heartbeat_minute, second=0, microsecond=0
            )
            if target <= now_local:
                target += timedelta(days=1)
            heartbeat_first = (target - now_local).total_seconds()
            next_mark = target
        else:
            # Wall-clock grid within the hour: ticks every HEARTBEAT_INTERVAL_SECONDS,
            # anchored so one tick falls on minute HEARTBEAT_MINUTE (e.g. 900s + minute 45 -> :00/:15/:30/:45).
            # After restart, first run is the next grid point, not "same minute + 1 hour".
            anchor = (heartbeat_minute * 60) % int(hi)
            seconds_in_hour = (
                now_local.minute * 60
                + now_local.second
                + now_local.microsecond / 1_000_000
            )
            delta = (anchor - seconds_in_hour) % hi
            if delta < 1e-9:
                delta = float(hi)
            heartbeat_first = delta
            next_mark = now_local + timedelta(seconds=delta)
        jq.run_repeating(
            _job_heartbeat,
            interval=heartbeat_interval,
            first=heartbeat_first,
            name="heartbeat",
        )
        if hi_i >= 86400:
            logging.info(
                "heartbeat scheduled: interval=%ss wall=%02d:%02d local first in %.1fs at %s",
                heartbeat_interval,
                heartbeat_hour,
                heartbeat_minute,
                heartbeat_first,
                next_mark.isoformat(timespec="seconds"),
            )
        else:
            logging.info(
                "heartbeat scheduled: interval=%ss minute=%s first in %.1fs at %s",
                heartbeat_interval,
                heartbeat_minute,
                heartbeat_first,
                next_mark.isoformat(timespec="seconds"),
            )
    else:
        logging.info("heartbeat disabled (HEARTBEAT_INTERVAL_SECONDS <= 0)")

    logging.info(
        "email2telegram v%s started | poll=%ss | allowlist=%s | export=%s | state=%s",
        service_version,
        poll_interval,
        sorted(allowed),
        export_dir.resolve() if export_dir else None,
        state_path,
    )

    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
