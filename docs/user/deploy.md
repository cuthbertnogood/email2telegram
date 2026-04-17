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
