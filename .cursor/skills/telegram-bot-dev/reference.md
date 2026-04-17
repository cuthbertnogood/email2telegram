# telegram-bot-dev reference

Short, copy-ready templates for this repository.

## 1) CommandHandler template

```python
from telegram.ext import CommandHandler, ContextTypes, filters


async def _cmd_status(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    bd = context.application.bot_data
    ver = bd["service_version"]
    await update.message.reply_text(f"email2telegram v{ver}: bot is running")


def register_handlers(application, allowed: frozenset[int]) -> None:
    chat_filter = filters.Chat(chat_id=list(allowed))
    application.add_handler(CommandHandler("status", _cmd_status, filters=chat_filter))
```

Why this shape:
- `filters.Chat(...)` keeps command access consistent with allowlist policy.
- `bot_data` avoids repeated env reads and keeps dependencies explicit.

## 2) JobQueue template

```python
import asyncio
import logging
from telegram.ext import ContextTypes


def _blocking_probe(client) -> int:
    # Example: sync/IO-heavy call.
    return client.count_unread()


async def _job_healthcheck(context: ContextTypes.DEFAULT_TYPE) -> None:
    bd = context.application.bot_data
    client = bd["imap_client"]
    try:
        unread = await asyncio.to_thread(_blocking_probe, client)
        logging.info("healthcheck: unread=%s", unread)
    except Exception:
        logging.exception("healthcheck job failed")


def register_jobs(application) -> None:
    jq = application.job_queue
    if jq is None:
        raise RuntimeError("JobQueue unavailable; install python-telegram-bot[job-queue]")
    jq.run_repeating(_job_healthcheck, interval=120.0, first=10.0)
```

Why this shape:
- `asyncio.to_thread(...)` prevents blocking the event loop.
- Exceptions are logged with stack traces but do not crash the process.

## 3) send_formatted_text template

```python
from telegram_client import send_formatted_text


async def notify_text(context, text: str) -> None:
    bd = context.application.bot_data
    await send_formatted_text(
        bot_token=bd["bot_token"],
        chat_id=bd["chat_id"],
        text=text,
        service_version=bd["service_version"],
        allowed_chat_ids=bd["allowed_chat_ids"],
    )
```

Why this shape:
- Reuses version banner and chunk splitting from project defaults.
- Keeps allowlist validation in one sender path instead of duplicated checks.
