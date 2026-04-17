from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, ContextTypes, filters

from allowlist import parse_allowed_chat_ids
from imap_client import ImapClient
from pipeline import load_export_dir_from_env, run_delivery_cycle
from state import StateStore
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


async def _cmd_start(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        ver = context.application.bot_data["service_version"]
        await update.message.reply_text(
            f"email2telegram v{ver}: почта доставляется в этот чат."
        )


def main() -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    imap_host = _required_env("IMAP_HOST")
    imap_port = int(os.getenv("IMAP_PORT", "993"))
    imap_user = _required_env("IMAP_USER")
    imap_pass = _required_env("IMAP_PASS")
    imap_mailbox = os.getenv("IMAP_MAILBOX", "INBOX")
    poll_interval = float(os.getenv("POLL_INTERVAL_SECONDS", "45"))

    bot_token = _required_env("TELEGRAM_BOT_TOKEN")
    chat_id = _required_env("TELEGRAM_CHAT_ID")
    allowed = parse_allowed_chat_ids(_required_env("TELEGRAM_ALLOWED_CHAT_IDS"))

    chat_id_int = int(chat_id)
    if chat_id_int not in allowed:
        raise RuntimeError("TELEGRAM_CHAT_ID must be included in TELEGRAM_ALLOWED_CHAT_IDS")

    export_dir = load_export_dir_from_env()
    state_path = _state_path()

    imap_client = ImapClient(
        host=imap_host,
        port=imap_port,
        user=imap_user,
        password=imap_pass,
        mailbox=imap_mailbox,
    )
    state = StateStore(path=state_path)
    service_version = get_version()

    application = Application.builder().token(bot_token).build()

    application.bot_data.update(
        {
            "imap_client": imap_client,
            "state": state,
            "chat_id": chat_id,
            "export_dir": export_dir,
            "allowed_chat_ids": allowed,
            "service_version": service_version,
        }
    )

    chat_filter = filters.Chat(chat_id=list(allowed))
    application.add_handler(CommandHandler("start", _cmd_start, filters=chat_filter))

    jq = application.job_queue
    if jq is None:
        raise RuntimeError("JobQueue unavailable; pip install 'python-telegram-bot[job-queue]'")
    jq.run_repeating(_poll_imap, interval=poll_interval, first=5.0)

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
