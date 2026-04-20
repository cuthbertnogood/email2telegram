# Environment Variables

Deploy scripts (`release.sh`, `host_to_vps.sh`, `host_to_docker_hub.sh`) load `.env` as **dotenv** (`KEY=value` lines only), not as a shell script — values may contain `;` or spaces without breaking bash.

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
- `HEARTBEAT_INTERVAL_SECONDS` (default `900`; use `0` to disable the heartbeat job)
- `HEARTBEAT_MINUTE` (default `45`): anchor minute (0–59) for the heartbeat wall-clock grid: ticks every `HEARTBEAT_INTERVAL_SECONDS` within the hour, with one tick on that minute; after restart the first run is the **next** grid point. With defaults (`900` / `45`) ticks fall at `:00`, `:15`, `:30`, `:45` in the process timezone (`TZ` in Docker if needed). If `HEARTBEAT_INTERVAL_SECONDS` does not divide 3600 evenly, the anchor is reduced modulo the interval.
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
