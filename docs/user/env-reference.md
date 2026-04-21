# Environment Variables

Deploy scripts (`release.sh`, `host_to_vps.sh`, `host_to_docker_hub.sh`) load `.env` as **dotenv** (`KEY=value` lines only), not as a shell script — values may contain `;` or spaces without breaking bash. A mistaken leading `;` before `KEY=value` (INI paste) is stripped; `sync-env` turns bare `; comment` lines into `# comment` so Docker Compose accepts the file.

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
- `HEARTBEAT_INTERVAL_SECONDS` (default `86400` = once per day; use `0` to disable the heartbeat job). Values **≥ 86400** must be a **multiple of 86400** (whole days; e.g. `172800` = every 2 days).
- `HEARTBEAT_HOUR` (default `9`, 0–23): local hour for the daily tick when `HEARTBEAT_INTERVAL_SECONDS` ≥ 86400 (ignored for shorter intervals).
- `HEARTBEAT_MINUTE` (default `0`, 0–59): with daily interval, local minute at `HEARTBEAT_HOUR`; with shorter `HEARTBEAT_INTERVAL_SECONDS`, anchor **minute within the hour** for the intra-hour grid (e.g. `900` + minute `45` → ticks at `:00`, `:15`, `:30`, `:45` in the process timezone). After restart, the first run is the **next** scheduled point.
- `EXPORT_MAIL_DIR` (saves `{uid}.eml`)
- `STATE_FILE` (default `.state.json`; in Docker use `/data/.state.json`)
- `TZ` (timezone for container logs)

## Deploy/Release Variables (PC)

- `DOCKER_USER`
- `TAG` (default `latest`)
- `NO_BUMP=1` (skip MINOR bump in Hub publish script)
- `VPS_USER`, `VPS_HOST`
- `VPS_SSH_PORT`, `VPS_REMOTE_DIR`, `VPS_SSH_OPTS`, `VPS_SSH_VERBOSE`, `VPS_PULL_UP_RETRIES` (default `3`; `host_to_vps.sh` pull-up retries), `VPS_POST_SYNC_SLEEP` (`release.sh` only: pause seconds after sync before pull-up)
- `VPS_SYNC_ENV` (default `1`): set to `0` to disable the `sync-env` step in `release.sh` if you manage VPS `.env` manually

These PC-only keys (`DOCKER_USER`, `VPS_*`, `NO_BUMP`, `TAG`, `LLM_*`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) are stripped by `sync-env` and never leave the PC. Secret rotation workflow: edit `TELEGRAM_BOT_TOKEN` / `IMAP_PASS` in local `.env`, run `./scripts/release.sh`.
