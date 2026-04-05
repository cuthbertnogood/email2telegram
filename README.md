# email2telegram (MVP)

Simple bridge: **connect your Yandex Mail mailbox** over IMAP, poll for new messages, and forward them to a Telegram chat. (Other IMAP servers work if you set `IMAP_HOST` accordingly.)

**Version:** see the [`VERSION`](VERSION) file at the repo root. Human-readable history: [`CHANGELOG.md`](CHANGELOG.md). Each Telegram delivery is prefixed with the running service version.

- After changing code under `src/` or `requirements.txt`, run `python3 scripts/bump_code_patch.py` to bump **PATCH** and refresh the fingerprint (commit `VERSION` and `.version/code_fingerprint` with your changes).
- Each **Docker Hub** publish via **`./scripts/docker-hub-publish.sh`** (or `make hub-push` / `./scripts/docker-hub-vps.sh hub-build-push`, same script) bumps **MINOR** before the image build; commit the updated `VERSION` after publishing.

## Features (MVP)

- Connects to a **Yandex** mailbox via IMAP (`imap.yandex.com` / `imap.yandex.ru`).
- **Single pipeline:** fetch new messages → optional save as `.eml` → send **full plain-text body** to Telegram (split into several chat messages if over the Telegram limit) → mark **read** on the server → update `last_seen_uid`.
- IMAP polling every N seconds.
- No filters (all new mail in the chosen folder).
- Telegram text formatting lives in `src/message_format.py` (easy to change later, e.g. Markdown).
- **Allowlist:** `TELEGRAM_ALLOWED_CHAT_IDS` — почта уходит только в `TELEGRAM_CHAT_ID`, если он входит в список; команда `/start` обрабатывается только для чатов из списка (остальные пользователи не получают ответов).
- Stores `last_seen_uid` in a state file so restarts do not resend old mail.

## Docker (VPS)

Short version:

```bash
cp .env.example .env   # fill and chmod 600 .env
docker compose up -d --build
docker compose logs -f
```

Full checklist (firewall, systemd, backups, **Docker Hub**): see **[DEPLOY.md](DEPLOY.md)**.

Compose sets `STATE_FILE=/data/.state.json` and optional `TZ`. For `.eml` on disk add `EXPORT_MAIL_DIR=/data/mail_export` to `.env`. Logs from the container are rotated (10 MB × 3 files). The named volume `email2telegram_data` keeps state across restarts.

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

3. Copy `.env.example` to `.env` and set **`IMAP_USER`** / **`IMAP_PASS`**, **`TELEGRAM_BOT_TOKEN`**, **`TELEGRAM_CHAT_ID`**, and **`TELEGRAM_ALLOWED_CHAT_IDS`** (в личке обычно тот же числовой id, что и `TELEGRAM_CHAT_ID`; несколько id через запятую).

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
- `TELEGRAM_ALLOWED_CHAT_IDS` (required) — comma-separated chat IDs allowed to receive mail and `/start`; must include `TELEGRAM_CHAT_ID`.
- `TELEGRAM_CHAT_ID` (required) — destination chat for forwarded mail (must appear in the allowlist).
- `EXPORT_MAIL_DIR` (optional) — if set, each delivered message is also written as `{uid}.eml` under this directory.
- `STATE_FILE` (optional, default `.state.json`) — path to the UID cursor file; use `/data/.state.json` in Docker.

## Manual verification checklist

1. Send a new test email to the configured inbox.
2. Check Telegram: each message starts with `[email2telegram v…]`; then full headers and body (long bodies may arrive as several parts, numbered `1/n`).
3. Restart the service and verify previously forwarded email is not resent.
4. Send UTF-8 subject/body email and verify text is decoded correctly.
