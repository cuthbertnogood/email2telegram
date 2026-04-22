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

## Where configuration lives on the VPS

Default deploy directory is **`/opt/email2telegram`**. If you use another path, it is the value of **`VPS_REMOTE_DIR`** in your **PC** repo `.env` (used by `host_to_vps.sh` / `release.sh`).

| Path on VPS | Role |
|---------------|------|
| **`/opt/email2telegram/.env`** | Runtime settings for the app: IMAP, Telegram, `DOCKER_IMAGE`, `HEARTBEAT_*`, `TZ`, `POLL_INTERVAL_SECONDS`, etc. Loaded by Compose (`env_file` in [docker-compose.hub.yml](../../docker-compose.hub.yml)) and by the Python process. **Permissions:** should be `600` (`chmod 600 .env`). |
| **`/opt/email2telegram/docker-compose.hub.yml`** | Stack definition: image `DOCKER_IMAGE`, `env_file: .env`, `TZ` from `.env` (see `environment` in [docker-compose.hub.yml](../../docker-compose.hub.yml)), volume for state. Synced from the repo by `./scripts/host_to_vps.sh sync` (not by `sync-env`). |
| **`/opt/email2telegram/vps-update-hub.sh`** (+ optional `deploy/*.service` / `*.timer`) | Hub pull helper and systemd units for unattended image refresh. |

**Important:** Changing **only** `.env` does not affect a **running** container until you **recreate** it (`docker compose … up -d --force-recreate`). Restart without recreate can keep old environment.

**PC vs VPS `.env`:** Your **local** repo `.env` also holds **deploy-only** keys (`VPS_USER`, `VPS_HOST`, `VPS_REMOTE_DIR`, `DOCKER_USER`, …). Those are **not** copied to the VPS by `sync-env` (see [deploy-to-vps.md](../dev/deploy-to-vps.md#env-sync-filtering-rules)). The VPS `.env` is the file the container actually reads at runtime.

## How to apply settings after you change them

### 1. You changed runtime variables only (IMAP, Telegram, heartbeat, `TZ`, …)

**From your PC** (edit local `.env`, then):

```bash
./scripts/host_to_vps.sh sync-env && ./scripts/host_to_vps.sh pull-up
```

**On the VPS over SSH:**

```bash
cd /opt/email2telegram   # or your VPS_REMOTE_DIR
nano .env                # or vim
docker compose -f docker-compose.hub.yml up -d --force-recreate
```

`docker compose pull` is optional if the image tag did not change.

### 2. You changed application code or `Dockerfile` (need a new image)

Build/push from the PC, then update the VPS container:

```bash
NO_BUMP=1 ./scripts/host_to_docker_hub.sh   # or ./scripts/release.sh
./scripts/host_to_vps.sh pull-up
```

Use `./scripts/release.sh` when you also want tests, optional `.env` sync, and GitHub push in one go.

### 3. You changed `docker-compose.hub.yml` or `deploy/*` scripts

From the PC:

```bash
./scripts/host_to_vps.sh sync && ./scripts/host_to_vps.sh pull-up
```

## Operations

- Logs: `docker compose -f docker-compose.hub.yml logs -f`
- Stop: `docker compose -f docker-compose.hub.yml down`
- State: Docker volume `email2telegram_data`

## Heartbeat period (already deployed VPS)

Heartbeat, **`TZ`** (e.g. `Europe/Moscow` for “local” wall time), and related keys live in **VPS `.env`** — same file as all other runtime variables (see [Where configuration lives on the VPS](#where-configuration-lives-on-the-vps)). Apply changes with [How to apply settings](#how-to-apply-settings-after-you-change-them) (typically `sync-env` + `pull-up` from the PC).

### Variables

See [env-reference.md](env-reference.md) for full detail. Typical keys:

- `HEARTBEAT_INTERVAL_SECONDS` — once per day: `86400`; disable: `0`.
- `HEARTBEAT_HOUR` (0–23) and `HEARTBEAT_MINUTE` (0–59) — local wall time for the daily tick when the interval is ≥ 86400 seconds.
- `TZ` — process timezone (e.g. `Europe/Moscow`); used by the app and by Compose for the container.

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
