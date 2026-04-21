# Deploy On VPS

This service requires only outbound HTTPS to IMAP and Telegram. Do not expose app ports.

## Recommended Path (from your PC)

1. Publish image:

```bash
./scripts/host_to_docker_hub.sh
```

2. Sync deployment files:

```bash
./scripts/host_to_vps.sh sync
```

3. Pull and recreate container on VPS:

```bash
./scripts/host_to_vps.sh pull-up
```

For one-command release:

```bash
./scripts/release.sh
```

## First-Time VPS Setup

```bash
sudo mkdir -p /opt/email2telegram
sudo chown "$USER:$USER" /opt/email2telegram
cd /opt/email2telegram
```

Create `.env` on VPS, set secrets and `DOCKER_IMAGE`, then:

```bash
docker compose -f docker-compose.hub.yml pull
docker compose -f docker-compose.hub.yml up -d --force-recreate
docker compose -f docker-compose.hub.yml logs -f
```

## Operations

- Logs: `docker compose -f docker-compose.hub.yml logs -f`
- Stop: `docker compose -f docker-compose.hub.yml down`
- State: Docker volume `email2telegram_data`

## Heartbeat period (already deployed VPS)

Heartbeat is configured in **`.env`** next to `docker-compose.hub.yml` on the VPS (often `/opt/email2telegram`). Compose loads it as `env_file` — the running process only sees changes after you **recreate** the container (`up -d --force-recreate`).

### Variables

See [env-reference.md](env-reference.md) for full detail. Typical keys:

- `HEARTBEAT_INTERVAL_SECONDS` — once per day: `86400`; disable: `0`.
- `HEARTBEAT_HOUR` (0–23) and `HEARTBEAT_MINUTE` (0–59) — local wall time for the daily tick when the interval is ≥ 86400 seconds.
- `TZ` — process timezone (e.g. `Europe/Moscow`); affects when “local” heartbeat fires.

### Option A: from your PC (no manual SSH edit on VPS)

1. Edit **local** `.env` in the repo with the desired `HEARTBEAT_*` (and `TZ` if needed).
2. From repo root:

```bash
./scripts/host_to_vps.sh sync-env && ./scripts/host_to_vps.sh pull-up
```

`sync-env` pushes a filtered copy of `.env` to the VPS; `pull-up` runs `docker compose pull` and `up -d --force-recreate`.

To also publish a new image and run the full pipeline: `./scripts/release.sh`.

### Option B: on the VPS over SSH

```bash
cd /opt/email2telegram   # or your deploy directory
nano .env                # set HEARTBEAT_* and TZ as needed
docker compose -f docker-compose.hub.yml up -d --force-recreate
docker compose -f docker-compose.hub.yml logs --tail=30
```

`pull` is optional if only `.env` changed (no new image tag).

### Image version

Daily heartbeat with `HEARTBEAT_HOUR` and intervals that are multiples of `86400` require an **image built from current `src/main.py`**. If the VPS still runs an older image, updating `.env` alone is not enough — build/push a new image, then `pull-up` or `./scripts/release.sh`.

### Verify

After recreate, logs should show a line like `heartbeat scheduled:` with the new `interval` and, for daily mode, `wall=HH:MM local`.

## Rotating Secrets (Bot Token, IMAP Password)

If a secret was exposed — e.g. `TELEGRAM_BOT_TOKEN` leaked in logs or screenshots — rotate it from your PC only, no SSH needed:

1. Get a new value (for Telegram: `/revoke` in @BotFather → `/newtoken`, copy the new token).
2. Edit **local `.env`** on your PC, replace the old value (e.g. `TELEGRAM_BOT_TOKEN=...`).
3. Run `./scripts/release.sh`.

The release script pushes a filtered copy of the local `.env` to the VPS (stripping PC-only keys like `DOCKER_USER`, `VPS_*`, `LLM_*`), writes it with mode `600`, and runs `docker compose up -d --force-recreate`. The new container boots with the new token; the old token stops working as soon as BotFather revokes it.

Skip the `.env` push when you prefer to manage VPS secrets manually:

```bash
./scripts/release.sh --skip-env-sync
# or permanently, in local .env:
# VPS_SYNC_ENV=0
```

Do not paste raw `docker compose logs` with API URLs anywhere — the bot token appears in `api.telegram.org/bot<token>/...` query strings. Strip the URL or redact the token before sharing.
