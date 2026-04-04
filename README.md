# email2telegram (MVP)

Simple bridge: **connect your Yandex Mail mailbox** over IMAP, poll for new messages, and forward them to a Telegram chat. (Other IMAP servers work if you set `IMAP_HOST` accordingly.)

## Features (MVP)

- Connects to a **Yandex** mailbox via IMAP (`imap.yandex.com` / `imap.yandex.ru`).
- IMAP polling every N seconds.
- Forwards all new emails (no filters).
- Sends `From`, `Subject`, `Date`, and body snippet to Telegram.
- Stores `last_seen_uid` in local state file to avoid duplicates after restart.

## Requirements

- Python 3.12+
- Yandex Mail (or compatible IMAP) credentials
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

3. Copy `.env.example` to `.env` and set **`IMAP_USER`** / **`IMAP_PASS`** (and Telegram vars when you run the full bridge).

### Yandex Mail (IMAP)

- Open [Yandex ID → Security](https://id.yandex.ru/security) for the same account as the mailbox.
- Create a **password for an external application** («Пароли приложений» / «Пароль для приложения»). Put it in **`IMAP_PASS`**.
- **`IMAP_USER`**: full address — `name@yandex.ru`, `name@yandex.com`, `name@ya.ru`, or a domain on Yandex 360.
- **`IMAP_HOST=imap.yandex.com`**, **`IMAP_PORT=993`**. If login fails, try **`imap.yandex.ru`**.
- In Yandex Mail settings, enable access for **mail clients** / IMAP if you see that option.

4. **Verify IMAP (no Telegram):**

   ```bash
   python src/imap_probe.py
   ```

   If mail is in another folder (not `INBOX`), list folders and set `IMAP_MAILBOX` in `.env`:

   ```bash
   python src/imap_probe.py --list-folders
   ```

   Optional: preview more messages — `python src/imap_probe.py --last 5`.

5. Run the full bridge (needs Telegram vars in `.env`):

   ```bash
   python src/main.py
   ```

### If you see `AUTHENTICATIONFAILED` / Invalid credentials

The server rejected `IMAP_USER` / `IMAP_PASS`. For Yandex, check:

- **App password**: with two-factor auth you need a [password for an app](https://yandex.ru/support/id/authorization/app-passwords.html), not the password from the browser.
- **Full login**: `IMAP_USER` must be the complete email address.
- **Host**: `imap.yandex.com` or `imap.yandex.ru`.
- **`.env`**: no accidental spaces; quotes only if the value contains spaces.
- **venv**: `which python` should point inside `.venv/` after `source .venv/bin/activate`. If not, recreate the venv: `rm -rf .venv && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.

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
