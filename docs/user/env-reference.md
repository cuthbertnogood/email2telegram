# Environment Variables

## Required

- `IMAP_HOST`
- `IMAP_USER`
- `IMAP_PASS`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `TELEGRAM_ALLOWED_CHAT_IDS`

## Optional

- `IMAP_PORT` (default `993`)
- `IMAP_MAILBOX` (default `INBOX`)
- `POLL_INTERVAL_SECONDS` (default `45`)
- `EXPORT_MAIL_DIR` (saves `{uid}.eml`)
- `STATE_FILE` (default `.state.json`; in Docker use `/data/.state.json`)
- `TZ` (timezone for container logs)

## Deploy/Release Variables (PC)

- `DOCKER_USER`
- `TAG` (default `latest`)
- `NO_BUMP=1` (skip MINOR bump in Hub publish script)
- `VPS_USER`, `VPS_HOST`
- `VPS_SSH_PORT`, `VPS_REMOTE_DIR`, `VPS_SSH_OPTS`, `VPS_SSH_VERBOSE`
