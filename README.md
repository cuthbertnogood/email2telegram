# email2telegram (MVP)

Simple bridge that polls an IMAP inbox and forwards new emails to a Telegram chat.

## Features (MVP)

- IMAP polling every N seconds.
- Forwards all new emails (no filters).
- Sends `From`, `Subject`, `Date`, and body snippet to Telegram.
- Stores `last_seen_uid` in local state file to avoid duplicates after restart.

## Requirements

- Python 3.12+
- IMAP mailbox credentials
- Telegram bot token and chat ID

## Setup

1. Install dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Create env file:

   ```bash
   cp .env.example .env
   ```

3. Fill `.env` values.

4. Run:

   ```bash
   python src/main.py
   ```

## Environment variables

- `IMAP_HOST` (required)
- `IMAP_PORT` (default `993`)
- `IMAP_USER` (required)
- `IMAP_PASS` (required)
- `IMAP_MAILBOX` (default `INBOX`)
- `POLL_INTERVAL_SECONDS` (default `45`)
- `TELEGRAM_BOT_TOKEN` (required)
- `TELEGRAM_CHAT_ID` (required)

## Manual verification checklist

1. Send a new test email to the configured inbox.
2. Check Telegram: one message appears with `From/Subject/Date` and snippet.
3. Restart the service and verify previously forwarded email is not resent.
4. Send UTF-8 subject/body email and verify text is decoded correctly.
