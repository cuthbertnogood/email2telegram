# Publish To Docker Hub

Script:

```bash
./scripts/host_to_docker_hub.sh
```

What it does:

- Optionally bumps `VERSION` MINOR.
- Builds `linux/amd64` and `linux/arm64` image via buildx.
- Pushes tags:
  - `${DOCKER_USER}/email2telegram:${TAG:-latest}`
  - `${DOCKER_USER}/email2telegram:<git-sha>`

Requirements:

- `docker login` done for current session.
- `.env` has `DOCKER_USER`.

Skip version bump:

```bash
NO_BUMP=1 ./scripts/host_to_docker_hub.sh
./scripts/host_to_docker_hub.sh --no-bump
```
