# Deploy on a VPS (Docker)

The bot only needs **outbound** HTTPS (IMAP + Telegram). **Do not** publish container ports to the internet.

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

**Versioning (short):** `VERSION` at the repo root is `MAJOR.MINOR.PATCH`. **PATCH** increases when you run `python3 scripts/bump_code_patch.py` after edits to `src/**/*.py` or `requirements.txt` (updates `.version/code_fingerprint`). **MINOR** increases automatically **before** each Hub image build when you use the scripted flows below—commit the new `VERSION` after a successful push.

```bash
cd /path/to/email2telegram
docker login -u YOUR_DOCKERHUB_USER
# Optional smoke test (no MINOR bump): read version into label
# v=$(tr -d '[:space:]' < VERSION); docker build --build-arg "APP_VERSION=$v" -t email2telegram:local .
docker build -t YOUR_DOCKERHUB_USER/email2telegram:latest .
docker push YOUR_DOCKERHUB_USER/email2telegram:latest
```

Manual `docker build` / `docker push` as above does **not** bump **MINOR**; prefer:

Or: `make hub-push DOCKER_USER=YOUR_DOCKERHUB_USER` (bumps **MINOR**, passes `APP_VERSION`, builds, pushes `:latest` and `:$GIT_SHA`).

Or: after `docker login`, `DOCKER_USER=YOUR_DOCKERHUB_USER ./scripts/docker-hub-vps.sh hub-build-push`. UI steps for the Hub repo and PAT: `./scripts/docker-hub-vps.sh hub-checklist`.

After a successful push, the image is visible under **Repositories** on app.docker.com.

### D. GitHub Actions (optional)

Add repository secrets `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`, then run workflow **Docker Hub** manually or push a tag `v1.0.0`. Images: `USERNAME/email2telegram:latest` and `:GITHUB_SHA`.

### E. VPS — pull from Hub and run

On the server you only need `docker-compose.hub.yml`, `.env`, and Docker — **full git clone is optional**.

From your PC (after `/opt/email2telegram` exists and is owned by your user on the VPS): `./scripts/docker-hub-vps.sh scp-compose YOUR_USER@VPS_HOST` copies `docker-compose.hub.yml` and `deploy/email2telegram.service` into that directory.

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
docker compose -f docker-compose.hub.yml up -d
docker compose -f docker-compose.hub.yml logs -f
```

Or from that directory: `make vps-pull`.

**Private image on VPS:** once per server, `docker login` with the same Hub user (or a robot account with pull access), then `pull` works.

`pull_policy: always` in `docker-compose.hub.yml` helps use the newest `latest` after each `pull`.

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

- **Hub:** `docker compose -f docker-compose.hub.yml pull && docker compose -f docker-compose.hub.yml up -d` — or from your PC: `./scripts/docker-hub-vps.sh vps-up-remote YOUR_USER@VPS_HOST`
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

## 7. Operations


| Action       | Command                                                                                                                                          |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Logs         | `docker compose -f docker-compose.hub.yml logs -f` (or default compose file)                                                                     |
| Stop         | `docker compose -f docker-compose.hub.yml down`                                                                                                  |
| State volume | named `email2telegram_data`                                                                                                                      |
| Backup state | copy `/var/lib/docker/volumes/...` or use `docker run --rm -v email2telegram_data:/data -v $(pwd):/backup alpine tar czf /backup/data.tgz /data` |


## 8. Secrets

Keep `.env` only on the server (`chmod 600`). Rotate IMAP app password and bot token if they ever leak.