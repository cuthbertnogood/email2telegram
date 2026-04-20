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
