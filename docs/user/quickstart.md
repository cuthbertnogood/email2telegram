# Quickstart

## Requirements

- Python 3.12+
- IMAP account credentials (Yandex Mail by default)
- Telegram bot token and destination chat ID

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set these required values in `.env`:

- `IMAP_USER`
- `IMAP_PASS`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `TELEGRAM_ALLOWED_CHAT_IDS` (must include `TELEGRAM_CHAT_ID`)

## Validate IMAP

```bash
python src/imap_probe.py
```

If mail is not in `INBOX`, discover folders:

```bash
python src/imap_probe.py --list-folders
```

## Run The Bridge

```bash
python src/main.py
```

## Verify Delivery

1. Send a test email to the configured inbox.
2. Check Telegram delivery with version prefix.
3. Restart the service and verify old messages are not resent.
