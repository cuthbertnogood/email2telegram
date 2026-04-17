---
name: telegram-bot-dev
description: Extend the email2telegram bot following this repo conventions (python-telegram-bot v21, JobQueue, allowlist, version banner, split_for_telegram, asyncio.to_thread for blocking IO). Use when adding Telegram commands, JobQueue jobs, modifying message sending, or editing src/main.py, src/telegram_client.py, src/pipeline.py, src/message_format.py, src/allowlist.py.
---

# Telegram Bot Dev (email2telegram)

## Quick start

- Entry point and wiring live in `src/main.py`.
- Delivery loop is `JobQueue -> _poll_imap -> run_delivery_cycle`.
- IMAP and file operations run through `asyncio.to_thread(...)`.
- Telegram delivery goes through `send_formatted_text` in `src/telegram_client.py`.
- Text shape/splitting lives in `src/message_format.py`.
- Allowlist is parsed in `src/allowlist.py` and enforced in handlers plus sender.

## When to apply this skill

Use this skill when the task includes at least one of:

- adding/changing a Telegram command handler;
- adding/changing a periodic job in `JobQueue`;
- modifying delivery text or Telegram sending behavior;
- editing `src/main.py`, `src/telegram_client.py`, `src/pipeline.py`, `src/message_format.py`, `src/allowlist.py`.

## Non-negotiable invariants

1. Send to Telegram via `send_formatted_text`, not direct `Bot.send_message`.
2. Register command handlers with `filters.Chat(chat_id=list(allowed))`.
3. Keep `TELEGRAM_CHAT_ID` inside `TELEGRAM_ALLOWED_CHAT_IDS`.
4. Wrap blocking IO in `await asyncio.to_thread(...)`.
5. Put shared runtime dependencies in `application.bot_data`, not globals.

## Add a command (minimal workflow)

1. Add `async def _cmd_xxx(update, context): ...` in `src/main.py`.
2. Read needed dependencies from `context.application.bot_data`.
3. Register with `application.add_handler(CommandHandler(..., filters=chat_filter))`.
4. Reuse existing `chat_filter = filters.Chat(chat_id=list(allowed))`.

Full template: see `reference.md`.

## Add a JobQueue task (minimal workflow)

1. Add `async def _job_xxx(context): ...` in `src/main.py`.
2. Read dependencies from `context.application.bot_data`.
3. Wrap blocking work in `await asyncio.to_thread(...)`.
4. Register through `jq.run_repeating(...)` after checking `jq is not None`.
5. Log failures with `logging.exception(...)`.

Full template: see `reference.md`.

## Sending long/structured text

- If message length can exceed Telegram limits, use `send_formatted_text`.
- Keep banner behavior (`service_version`) and chunking behavior (`split_for_telegram`).
- To change output content, edit `format_email_plain` in `src/message_format.py`.
- To change chunk strategy, edit `split_for_telegram` in `src/message_format.py`.

## State and persistence

- Persistent cursor and dedup data go through `StateStore` (`src/state.py`).
- Access store as `context.application.bot_data["state"]`.
- Call state/file methods via `asyncio.to_thread` from async code.

## Run and verify quickly

- IMAP-only check: `python src/imap_probe.py`.
- Extra IMAP checks: `python src/imap_probe.py --list-folders`, `python src/imap_probe.py --last 5`.
- Full bridge with log file: `./scripts/run-with-log.sh python src/main.py`.
- Read run log at `logs/last-run.log`.

## Release discipline for this repo

- If you changed `src/**` or `requirements.txt`, run `python3 scripts/bump_code_patch.py`.
- For Docker Hub publish use `./scripts/host_to_docker_hub.sh` (MINOR bump by default).
- Keep human-readable notes in `CHANGELOG.md`.

## Anti-patterns to avoid

- Direct `Bot(token).send_message(...)` for delivery pipeline messages.
- New command handler without allowlist chat filter.
- Blocking IMAP/file operations directly inside async handlers/jobs.
- Reading env vars inside handlers/jobs when value can be put in `bot_data` once.
- Hardcoded chat IDs instead of env + allowlist.

## Additional resources

- Extended templates: `reference.md`.
