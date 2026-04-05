# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Changed

- Hub deploy path: `vps-update-hub.sh`, `vps-up-remote`, `make vps-pull`, and `deploy/email2telegram.service` now run `docker compose … up -d --force-recreate` after `pull` so the container is recreated from the new image. `DEPLOY.md` adds version-sync notes (local publish vs CI tag) and VPS verification commands (`/app/VERSION`, OCI label).

## [0.4.1] - 2026-04-05

### Changed

- `VERSION` set to **0.4.1**.
- `DEPLOY.md`: Markdown/link formatting in the Hub deploy and periodic-pull sections; tighter list layout under “Get the new image onto the VPS”.
- `docs/docker-vps-architecture.md`: wider host-components table, spacing around Mermaid blocks, and normalized line endings (LF).

## [0.3.1] - 2026-04-05

### Added

- Semantic version in root `VERSION` (MAJOR.MINOR.PATCH) and runtime read via `src/version.py`.
- Code fingerprint at `.version/code_fingerprint` and script `scripts/bump_code_patch.py` to bump **PATCH** when `src/**/*.py` or `requirements.txt` change.
- Script `scripts/bump_docker_minor.py`; Docker Hub push path bumps **MINOR** before build (`scripts/docker-hub-vps.sh`, `make hub-push`).
- Version banner before each outgoing Telegram message; `/start` and startup log include service version.
- `Dockerfile` copies `VERSION` and sets `org.opencontainers.image.version` via build-arg `APP_VERSION`.
- Email parsing: stable `dedup_key` from normalized `Message-ID` / `Message-Id`, or SHA-256 of raw RFC822 when absent; parsed output includes `message_id`.
- State store keeps a bounded list of delivered dedup keys so the same logical message is not posted twice if IMAP returns overlapping UIDs.
- GitHub Actions: Docker publish with **buildx** for **linux/amd64** and **linux/arm64**, passing `APP_VERSION` from `VERSION`.
- `scripts/docker-hub-publish.sh` for Docker Hub publish; `scripts/docker-hub-vps.sh` and `make hub-push` orchestrate local build and push.
- `deploy/vps-update-hub.sh`, `deploy/email2telegram-hub-update.service`, and `deploy/email2telegram-hub-update.timer` for periodic pull/restart from Hub on a VPS.
- `docs/docker-hub-build-and-vps-plan.md` — step-by-step Hub build and VPS update notes.

### Changed

- IMAP delivery pipeline: drops UIDs not after `last_seen_uid`, logs poll UID diagnostics, records dedup keys after successful Telegram delivery, and skips already-delivered keys while still advancing processed UIDs.
- `DEPLOY.md` expanded for Docker Hub, VPS updates, and timer-based refresh.
