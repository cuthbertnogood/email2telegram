# Publishing the image to Docker Hub

This guide covers **`scripts/host_to_docker_hub.sh`**: bump **MINOR** in `VERSION`, build a multi-arch image with **buildx**, and **push** to Docker Hub.

For putting the image on a server, use **[DEPLOY.md](../DEPLOY.md)**, **`scripts/host_to_vps.sh`**, and **[host-to-vps.md](host-to-vps.md)**.

---

## Prerequisites

- **Docker** with **Buildx** and a builder that can `--push` (default Docker Desktop or a configured `docker buildx` builder).
- **Docker Hub** account and repository `email2telegram` (create it in the Hub UI if needed).
- **PAT** (personal access token) for `docker login` — [Hub security settings](https://hub.docker.com/settings/security).
- Run commands from **any directory**; the script changes to the repository root automatically.

---

## One-time: `docker login`

```bash
docker login -u YOUR_DOCKERHUB_USER
# password = PAT
```

Do **not** put the PAT in `.env` (risk of leaks). Login is a separate step before each push session (credentials are usually cached by Docker).

---

## Configuration (`.env` in repo root)

| Variable | Required | Description |
| -------- | -------- | ----------- |
| `DOCKER_USER` | Yes (for push) | Docker Hub username or organization. |
| `TAG` | No | Image tag, default `latest`. |
| `NO_BUMP` | No | If set to `1`, the script does **not** increment **MINOR** in `VERSION` before build. |

The script **sources** `.env` before reading these values.

**Shell wins for `DOCKER_USER`:** if `DOCKER_USER` is already set in the environment when you run the script, `.env` does **not** override it. Use that to push under a different Hub user once: `DOCKER_USER=otherorg ./scripts/host_to_docker_hub.sh`.

See also **[.env.example](../.env.example)**.

---

## What the script does

1. **By default:** increments **MINOR** in the root **`VERSION`** file (same idea as the old Python helper; implemented in bash).
2. Runs **`docker buildx build`** for **`linux/amd64`** and **`linux/arm64`** with **`--push`**.
3. Tags pushed:
   - `${DOCKER_USER}/email2telegram:${TAG}` (default tag `latest`)
   - `${DOCKER_USER}/email2telegram:<git-short-sha>` or `:local` if not in a git repo

Build-arg **`APP_VERSION`** is taken from `VERSION` after the optional bump.

---

## Run

```bash
./scripts/host_to_docker_hub.sh
```

Equivalent:

```bash
make hub-push
```

(`make hub-push` forwards `DOCKER_USER` and `TAG` from the Make environment into the script.)

### Skip MINOR bump

Either:

```bash
NO_BUMP=1 ./scripts/host_to_docker_hub.sh
```

or:

```bash
./scripts/host_to_docker_hub.sh --no-bump
```

### Help

```bash
./scripts/host_to_docker_hub.sh --help
```

---

## After a successful push

If **MINOR** was bumped, **commit** the updated **`VERSION`** file (and push to git if you track releases that way).

**PATCH** version bumps for code changes are separate: run **`python3 scripts/bump_code_patch.py`** when you change `src/**/*.py` or `requirements.txt` (see README). The Hub script only bumps **MINOR** by default.

---

## GitHub Actions

The workflow **[.github/workflows/docker-publish.yml](../.github/workflows/docker-publish.yml)** builds and pushes from CI **without** auto-bumping **MINOR**. The image uses **`VERSION`** from the commit that triggered the workflow.

---

## Troubleshooting

| Issue | What to check |
| ----- | --------------- |
| `DOCKER_USER` unset | Set in `.env` or export before running. |
| Push denied | Run `docker login`; PAT scopes; repo name `email2telegram` exists under that user/org. |
| Buildx / push errors | `docker buildx ls`; builder must support multi-platform push. |
| Wrong image on VPS | `DOCKER_IMAGE` in the server `.env` must match `${DOCKER_USER}/email2telegram` and tag — see [DEPLOY.md](../DEPLOY.md). |

---

## Next: deploy on a VPS

Sync compose and deploy files, then pull the new image on the server: **[DEPLOY.md](../DEPLOY.md)** and **`./scripts/host_to_vps.sh`** (see **[host-to-vps.md](host-to-vps.md)**).

For component-level diagrams (Compose, volumes, systemd), see **[docker-vps-architecture.md](docker-vps-architecture.md)**.
