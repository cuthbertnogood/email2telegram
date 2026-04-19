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
- `VPS_PULL_UP_RETRIES` — max SSH attempts for `pull-up` / `deploy` (default `3`; transient “connection closed” retries with 5s, then 10s, … sleep between tries).

## Examples

```bash
./scripts/host_to_vps.sh sync
./scripts/host_to_vps.sh pull-up
./scripts/host_to_vps.sh deploy
./scripts/host_to_vps.sh -p 2222 sync
./scripts/host_to_vps.sh sync deploy@203.0.113.10 /srv/email2telegram
```

## Troubleshooting

### `sync` works but `pull-up` prints `Connection closed by HOST port …`

`sync` uses `scp` (often SFTP under the hood). `pull-up` needs a normal **remote shell** to run `docker compose`. If the server closes the session immediately, common causes are:

1. **SFTP-only SSH account** — `Match User … ForceCommand internal-sftp` (or similar) allows file copy but not `ssh user@host 'cmd'`. Fix: allow an exec/shell for that user, or use a different UNIX user for deploy that has a full shell.
2. **Profile scripts exiting** — on the VPS, check `~/.bash_profile`, `~/.profile`, `~/.bashrc` for `exit` or a broken `exec` when the session is non-interactive.
3. **Resource or policy kills** — OOM during image pull, or SSH `MaxSessions` / fail2ban. On the VPS run `cd /opt/email2telegram && docker compose -f docker-compose.hub.yml pull` and check `dmesg` / `journalctl -u ssh`.

Diagnostics from your PC (same `VPS_SSH_PORT` / `VPS_SSH_OPTS` as in `.env`):

```bash
VPS_SSH_VERBOSE=1 ./scripts/host_to_vps.sh pull-up
ssh -p YOUR_PORT YOUR_USER@YOUR_HOST 'echo shell_ok'
```

`host_to_vps.sh` adds **ServerAlive** options by default to reduce idle disconnects during long pulls. **`pull-up` retries** the remote SSH up to `VPS_PULL_UP_RETRIES` times (default 3) with increasing sleep between attempts when the session drops before success.
