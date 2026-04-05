# Deploy on a VPS (Docker)

The bot only needs **outbound** HTTPS (IMAP + Telegram). **Do not** expose container ports to the internet.

- **Operational flow (build, Hub, `vps.sh`, CI):** [docs/docker-hub-build-and-vps-plan.md](docs/docker-hub-build-and-vps-plan.md)  
- **What runs where (diagrams):** [docs/docker-vps-architecture.md](docs/docker-vps-architecture.md)

---

## Docker Hub path (recommended)

### On your PC (repo `.env`)

| Variable | Purpose |
| -------- | ------- |
| `DOCKER_USER` | Docker Hub login; used by `./scripts/docker-hub-build-push.sh` |
| `VPS_USER`, `VPS_HOST` | SSH target for `./scripts/vps.sh` |
| `VPS_SSH_PORT` | If SSH is not on 22 |
| `VPS_REMOTE_DIR` | Remote project dir (default `/opt/email2telegram`) |
| `VPS_SSH_OPTS` | e.g. `-i ~/.ssh/key` |
| `VPS_SSH_VERBOSE` | Set to `1` for `ssh -v` if something breaks |

**Hub (browser):** create repo `email2telegram`, [PAT for `docker login`](https://hub.docker.com/settings/security). Cheatsheet: `./scripts/vps.sh hub-checklist`.

**Build and push** (before build, bumps **MINOR** in `VERSION` unless `NO_BUMP=1` or `--no-bump`; then `linux/amd64` + `linux/arm64` push):

```bash
docker login -u YOUR_DOCKERHUB_USER
./scripts/docker-hub-build-push.sh    # or: make hub-push
```

Also: `./scripts/docker-hub-publish.sh` (wrapper). After a bump, **commit `VERSION`**.

**Copy files to VPS** (after `sudo mkdir … && chown` on the server — see below):

```bash
./scripts/vps.sh sync
```

**First full deploy from PC** (needs **`.env` already on the VPS** with `DOCKER_IMAGE` + app secrets; private image: `docker login` once on VPS):

```bash
./scripts/vps.sh deploy    # sync + pull/up + Hub timer (sudo may prompt)
```

Remote `docker compose` runs under **`bash -lc`** so `docker` is on `PATH` like an interactive login.

**Troubleshooting SSH:** if you see `Connection closed by …` right after `sync`, run `VPS_SSH_VERBOSE=1 ./scripts/vps.sh pull-up` and check that on the VPS `docker compose version` works as the same SSH user.

### On the VPS (first time)

```bash
sudo mkdir -p /opt/email2telegram && sudo chown "$USER:$USER" /opt/email2telegram
cd /opt/email2telegram
nano .env   # IMAP_*, TELEGRAM_*, DOCKER_IMAGE=YOURHUB/email2telegram:latest, …
chmod 600 .env
docker compose -f docker-compose.hub.yml pull
docker compose -f docker-compose.hub.yml up -d --force-recreate
docker compose -f docker-compose.hub.yml logs -f
```

Or from project dir: `make vps-pull`. **Private image:** `docker login` on the VPS once.

### GitHub Actions (optional)

Secrets: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`. Trigger: workflow **Docker Hub** or tag `v*`. CI does **not** bump MINOR — set `VERSION` in the tagged commit.

---

## New image after a release

1. `docker login` if needed → `./scripts/docker-hub-build-push.sh` → commit **`VERSION`** if it changed.  
2. On VPS: wait for the Hub timer (~10 min) or from PC: `./scripts/vps.sh pull-up`.  
3. Check: `docker compose -f …/docker-compose.hub.yml ps`, `exec … cat /app/VERSION`.

Re-run **`deploy`** only if you changed compose, `vps-update-hub.sh`, or systemd units in git.

---

## Server without Hub (build on VPS)

```bash
sudo mkdir -p /opt/email2telegram && sudo chown "$USER:$USER" /opt/email2telegram
cd /opt/email2telegram && git clone <repo> .
cp .env.example .env && nano .env && chmod 600 .env
docker compose up -d --build && docker compose logs -f
```

## Firewall (example UFW)

```bash
sudo ufw default deny incoming && sudo ufw default allow outgoing
sudo ufw allow OpenSSH && sudo ufw enable
```

## Optional: systemd main service

After `./scripts/vps.sh sync`, unit files sit next to compose. See `./scripts/vps.sh systemd-hints` or copy `email2telegram.service` from `/opt/email2telegram` into `/etc/systemd/system/`, then `daemon-reload`, `enable --now`.

## Optional: Hub pull every ~10 min

`./scripts/vps.sh deploy` installs the timer. Manual: copy `deploy/email2telegram-hub-update.service` and `deploy/email2telegram-hub-update.timer` to `/etc/systemd/system/`, then `systemctl enable --now email2telegram-hub-update.timer`. Logs: `journalctl -u email2telegram-hub-update.service`.

## Operations

| Action | Command |
| ------ | ------- |
| Logs | `docker compose -f docker-compose.hub.yml logs -f` |
| Stop | `docker compose -f docker-compose.hub.yml down` |
| State | Docker volume `email2telegram_data` (backup: copy volume or `docker run … tar`) |

## Secrets

`.env` only on the server, `chmod 600`. Rotate IMAP app password and bot token if exposed.
