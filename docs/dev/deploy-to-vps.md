# Deploy To VPS From PC

Script:

```bash
./scripts/host_to_vps.sh <subcommand>
```

## Main Subcommands

- `sync`: copy `docker-compose.hub.yml` and `deploy/*` artifacts to VPS.
- `pull-up`: run remote `docker compose pull` + `up -d --force-recreate`.
- `enable-timer`: install and enable hub update systemd timer.
- `deploy`: `sync + pull-up + enable-timer`.

## Required Variables

- `VPS_USER`
- `VPS_HOST`

Optional:

- `VPS_SSH_PORT`
- `VPS_REMOTE_DIR` (default `/opt/email2telegram`)
- `VPS_SSH_OPTS`
- `VPS_SSH_VERBOSE=1`

## Examples

```bash
./scripts/host_to_vps.sh sync
./scripts/host_to_vps.sh pull-up
./scripts/host_to_vps.sh deploy
./scripts/host_to_vps.sh -p 2222 sync
./scripts/host_to_vps.sh sync deploy@203.0.113.10 /srv/email2telegram
```
