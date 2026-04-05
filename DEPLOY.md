# Deploy on a VPS (Docker)

The bot only needs **outbound** HTTPS (IMAP + Telegram). **Do not** publish container ports to the internet.

**End-to-end build chain (multi-arch, VERSION bumps, scripts, CI):** [docs/docker-hub-build-and-vps-plan.md](docs/docker-hub-build-and-vps-plan.md).

**Architecture (Docker on VPS — components, settings, diagrams):** [docs/docker-vps-architecture.md](docs/docker-vps-architecture.md).

## Docker Hub (recommended)

[Docker Hub](https://hub.docker.com/) opens from **[app.docker.com](https://app.docker.com/)** after sign-in. The image name is always `YOUR_DOCKERHUB_USERNAME/email2telegram:tag` (same string you put in `DOCKER_IMAGE` on the VPS).

### A. Create the repository on the web

1. Sign in at [app.docker.com](https://app.docker.com/) (or [hub.docker.com](https://hub.docker.com/)).
2. **Repositories** → **Create repository**.
3. Name: e.g. `email2telegram`, visibility **Private** or **Public**.
4. You do **not** upload the image in the browser — the site only reserves the name. The image appears after the first `**docker push`** (or GitHub Actions) with that name.

### B. Access token (for `docker login` on your PC / CI)

1. [Account settings → Security](https://hub.docker.com/settings/security) (or **Personal access tokens** in the app).
2. **New access token** → copy it once; use it as the password in `docker login` (username = your Docker Hub login).

### C. Build and push from your machine

**Versioning (short):** `VERSION` at the repo root is `MAJOR.MINOR.PATCH`. **PATCH** increases when you run `python3 scripts/bump_code_patch.py` after edits to `src/**/*.py` or `requirements.txt` (updates `.version/code_fingerprint`). **MINOR** increases automatically **before** each Hub image build when you use the publish script (or wrappers below)—commit the new `VERSION` after a successful push.

**Recommended — one script** (always runs `bump_docker_minor.py`, then multi-arch `buildx` + push):

```bash
cd /path/to/email2telegram
docker login -u YOUR_DOCKERHUB_USER
DOCKER_USER=YOUR_DOCKERHUB_USER ./scripts/docker-hub-publish.sh
```

Same behavior: `make hub-push DOCKER_USER=YOUR_DOCKERHUB_USER`, or `DOCKER_USER=YOUR_DOCKERHUB_USER ./scripts/docker-hub-vps.sh hub-build-push`. UI steps for the Hub repo and PAT: `./scripts/docker-hub-vps.sh hub-checklist`.

Manual `docker build` / `docker push` **without** the script does **not** bump **MINOR** and is easy to get wrong; use `./scripts/docker-hub-publish.sh` instead.

```bash
# Optional local smoke test only (no MINOR bump, no push):
# v=$(tr -d '[:space:]' < VERSION); docker build --build-arg "APP_VERSION=$v" -t email2telegram:local .
```

After a successful push, the image is visible under **Repositories** on app.docker.com.

### D. GitHub Actions (optional)

Add repository secrets `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`, then run workflow **Docker Hub** manually or push a tag `v1.0.0`. Images: `USERNAME/email2telegram:latest` and `:GITHUB_SHA`.

### E. VPS — pull from Hub and run

On the server you only need `docker-compose.hub.yml`, `.env`, and Docker — **full git clone is optional**.

From your PC (after `/opt/email2telegram` exists and is owned by your user on the VPS): `./scripts/docker-hub-vps.sh scp-compose YOUR_USER@VPS_HOST` copies `docker-compose.hub.yml`, `deploy/vps-update-hub.sh`, `deploy/email2telegram.service`, and Hub update timer units into that directory. Non-default SSH port: `-p PORT` before the subcommand or env `VPS_SSH_PORT`.

**One-shot Hub deploy from your PC** (after `.env` is on the VPS with `DOCKER_IMAGE` and secrets; for a **private** image run `docker login` on the VPS once first):

```bash
./scripts/docker-hub-vps.sh hub-deploy-vps YOUR_USER@VPS_HOST
```

This runs `scp-compose`, remote `docker compose pull && up -d --force-recreate`, then installs and enables `**email2telegram-hub-update.timer**` so the host pulls fresh Hub images every 10 minutes (see [section 7](#7-periodic-hub-pull-every-10-minutes-optional)). `ssh -t` is used so `sudo` can prompt for a password when copying unit files.

```bash
mkdir -p /opt/email2telegram && cd /opt/email2telegram
# copy docker-compose.hub.yml and .env (scp or nano)
```

In `**.env**` set among other variables:

```env
DOCKER_IMAGE=YOUR_DOCKERHUB_USER/email2telegram:latest
```

```bash
docker compose -f docker-compose.hub.yml pull
docker compose -f docker-compose.hub.yml up -d --force-recreate
docker compose -f docker-compose.hub.yml logs -f
```

Or from that directory: `make vps-pull`.

**Private image on VPS:** once per server, `docker login` with the same Hub user (or a robot account with pull access), then `pull` works.

`pull_policy: always` in `docker-compose.hub.yml` helps use the newest `latest` after each `pull`.

### F. New releases (every time you ship a new image)

**Version vs. git:** After a **local** `./scripts/docker-hub-publish.sh`, commit and push `VERSION` (step 4 below). **GitHub Actions** (tag `v*`) builds whatever `VERSION` is in the **tagged** commit — the workflow does not run `bump_docker_minor.py`; bump `VERSION` in that commit before tagging. Full matrix: [docs/docker-hub-build-and-vps-plan.md](docs/docker-hub-build-and-vps-plan.md).

Use this after the VPS is already set up (`.env`, stack running, optional [section 7](#7-periodic-hub-pull-every-10-minutes-optional) timer).

**1. On your PC — open a terminal and go to the repo:**

```bash
cd /path/to/email2telegram
```

**2. Log in to Docker Hub when needed** (token expires, new machine, or `docker push` denied):

```bash
docker login -u YOUR_DOCKERHUB_USER
```

**3. Build, bump MINOR in `VERSION`, push multi-arch image:**

```bash
DOCKER_USER=YOUR_DOCKERHUB_USER ./scripts/docker-hub-publish.sh
```

Wait until the script finishes without errors. The image on Hub will be `YOUR_DOCKERHUB_USER/email2telegram:latest` (and a second tag with the git short SHA).

**4. On your PC — commit the updated `VERSION` file** (the publish script always bumps MINOR before the build):

```bash
git add VERSION
git status
git commit -m "Bump VERSION after Docker Hub publish"
git push
```

**5. Get the new image onto the VPS — pick one:**

- **A — Automatic (recommended if the timer is enabled):** do nothing for up to ~10 minutes. On the VPS the service `email2telegram-hub-update` runs `docker compose pull` + `up -d --force-recreate` on a schedule (via `vps-update-hub.sh`). Check:
  ```bash
  # on the VPS
  journalctl -u email2telegram-hub-update.service -n 30 --no-pager
  docker compose -f /opt/email2telegram/docker-compose.hub.yml ps
  ```
- **B — Manual from your PC right after push** (SSH port 22):
  ```bash
  ./scripts/docker-hub-vps.sh vps-up-remote YOUR_USER@VPS_HOST
  ```
  Non-default SSH port (example: `2222`; use your server’s port):
  ```bash
  ./scripts/docker-hub-vps.sh -p 2222 vps-up-remote YOUR_USER@VPS_HOST
  ```
  Or with an env var:
  ```bash
  VPS_SSH_PORT=2222 ./scripts/docker-hub-vps.sh vps-up-remote YOUR_USER@VPS_HOST
  ```

**6. On the VPS — confirm the container is healthy:**

```bash
cd /opt/email2telegram
docker compose -f docker-compose.hub.yml ps
docker compose -f docker-compose.hub.yml logs --tail 50 email2telegram
```

**7. Confirm the running image matches the version you shipped** (embedded at build time):

```bash
docker compose -f docker-compose.hub.yml exec email2telegram cat /app/VERSION
docker inspect email2telegram --format '{{index .Config.Labels "org.opencontainers.image.version"}}'
docker compose -f docker-compose.hub.yml images
```

If `pull` succeeded but the version is still old, run `docker compose -f docker-compose.hub.yml up -d --force-recreate` (or re-run `vps-update-hub.sh` / `vps-up-remote` after upgrading those scripts from the repo).

**Note:** You do **not** need to re-run `hub-deploy-vps` for every release unless you changed compose files, `vps-update-hub.sh`, or systemd units in the repo.

## 1. Server

- Ubuntu 22.04/24.04 LTS or similar with SSH.
- Install [Docker Engine](https://docs.docker.com/engine/install/) and the [Compose plugin](https://docs.docker.com/compose/install/linux/). Quick reference: `./scripts/docker-hub-vps.sh vps-install-docker`

## 2. Firewall

Allow SSH only (example with UFW):

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw enable
```

No rules are required for this app’s inbound traffic.

## 3. Project on the server

**With Docker Hub:** put `docker-compose.hub.yml` and `.env` in e.g. `/opt/email2telegram` (see [Docker Hub](#docker-hub-recommended) above).

**Build on the server instead:** clone the full repo:

```bash
sudo mkdir -p /opt/email2telegram
sudo chown "$USER":"$USER" /opt/email2telegram
cd /opt/email2telegram
git clone <your-repo-url> .
```

## 4. Environment

```bash
cp .env.example .env
nano .env   # IMAP_*, TELEGRAM_*, TELEGRAM_ALLOWED_CHAT_IDS, TELEGRAM_CHAT_ID
chmod 600 .env
```

Inside the container, `STATE_FILE=/data/.state.json` is set by Compose so the UID cursor survives restarts in the Docker volume.

Optional: also persist `.eml` copies — in `.env` set:

```env
EXPORT_MAIL_DIR=/data/mail_export
```

Optional: server timezone for log timestamps:

```bash
echo 'TZ=Europe/Moscow' >> .env
```

## 5. Run

**Image from Docker Hub:**

```bash
docker compose -f docker-compose.hub.yml up -d
docker compose -f docker-compose.hub.yml logs -f
```

**Build on server (default `docker-compose.yml`):**

```bash
docker compose up -d --build
docker compose logs -f
```

Updates:

- **Hub:** `docker compose -f docker-compose.hub.yml pull && docker compose -f docker-compose.hub.yml up -d --force-recreate` — or from your PC: `./scripts/docker-hub-vps.sh vps-up-remote YOUR_USER@VPS_HOST`
- **Local build:** `git pull && docker compose up -d --build`

## 6. Auto-start on boot (optional)

Edit `deploy/email2telegram.service` in the repo — set `WorkingDirectory` to `/opt/email2telegram` (or your path), ensure `docker compose` path is `/usr/bin/docker` or `which docker`.

**Full git clone on the VPS** (paths relative to repo root):

```bash
sudo cp deploy/email2telegram.service /etc/systemd/system/
```

**Minimal Hub layout** (`scp-compose` or manual copy — unit file lies next to compose, not under `deploy/`):

```bash
sudo cp /opt/email2telegram/email2telegram.service /etc/systemd/system/
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now email2telegram.service
```

Same steps as a reminder: `./scripts/docker-hub-vps.sh systemd-hints`

## 7. Periodic Hub pull (every 10 minutes, optional)

To pick up new `latest` (or your tag) from Docker Hub without manual `pull`, enable the **systemd timer** below. It runs `[deploy/vps-update-hub.sh](deploy/vps-update-hub.sh)` on a fixed cadence (`pull` + `up -d --force-recreate`); logs go to the journal. The service unit uses `flock -n` so a long `pull` does not overlap the next scheduled run. The script calls `/usr/bin/docker` by default.

If you already ran `**./scripts/docker-hub-vps.sh hub-deploy-vps …`** (see **Docker Hub → E. VPS** above), this timer is already installed and started.

Otherwise, after `scp-compose` or a manual copy to `/opt/email2telegram`, install on the VPS:

```bash
sudo cp /opt/email2telegram/email2telegram-hub-update.service /etc/systemd/system/
sudo cp /opt/email2telegram/email2telegram-hub-update.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now email2telegram-hub-update.timer
sudo systemctl list-timers email2telegram-hub-update.timer
journalctl -u email2telegram-hub-update.service -n 50 --no-pager
```

If the project directory is not `/opt/email2telegram`, edit `WorkingDirectory`, `ExecStart` paths, and the lock file path in `email2telegram-hub-update.service` before `daemon-reload`.

Timer templates in the repo: `[deploy/email2telegram-hub-update.service](deploy/email2telegram-hub-update.service)`, `[deploy/email2telegram-hub-update.timer](deploy/email2telegram-hub-update.timer)`.

## 8. Operations


| Action       | Command                                                                                                                                          |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Logs         | `docker compose -f docker-compose.hub.yml logs -f` (or default compose file)                                                                     |
| Stop         | `docker compose -f docker-compose.hub.yml down`                                                                                                  |
| State volume | named `email2telegram_data`                                                                                                                      |
| Backup state | copy `/var/lib/docker/volumes/...` or use `docker run --rm -v email2telegram_data:/data -v $(pwd):/backup alpine tar czf /backup/data.tgz /data` |


## 9. Secrets

Keep `.env` only on the server (`chmod 600`). Rotate IMAP app password and bot token if they ever leak.