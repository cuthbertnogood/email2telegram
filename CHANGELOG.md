# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Structured documentation split by audience: `docs/user/*` for operators and `docs/dev/*` for project/release maintenance.
- README sync automation: `scripts/sync_readme_ru.py` with `--translate` and `--check`, plus marker hash validation in `README.ru.md`.
- Git hook tooling: `.githooks/pre-commit` and `scripts/install_git_hooks.sh` to enforce README sync locally.
- GitHub Actions workflow `.github/workflows/readme-sync.yml` to enforce README EN/RU sync on push/PR.

### Changed

- Root `README.md` and `README.ru.md` reduced to concise entry points with links to user/project docs.
- `DEPLOY.md` converted to a slim pointer to dedicated user/dev deployment docs.
- `scripts/release.sh` now performs README sync check before the test/build/deploy pipeline.

## [0.8.2] - 2026-04-17

### Added

- Startup notification in Telegram when container starts with a new app version on the same `/data` volume (`last_service_version` persisted in state).
- Unified release entrypoint: `scripts/release.sh` (tests -> Docker Hub push -> VPS sync -> remote pull/recreate in one command).
- `scripts/release.sh` now pushes project changes to GitHub by default after successful VPS deploy (disable with `--no-push-github`).

### Changed

- Delivery reliability: `StateStore` writes are now atomic (`tmp` + `os.replace`) to avoid corrupted state files on abrupt restarts.
- IMAP polling now fetches messages with `BODY.PEEK[]` and marks `\Seen` in a single UID `STORE` call; connection open/login/select has bounded retry with backoff.
- Telegram delivery now reuses `application.bot` and retries transient send errors (`RetryAfter`, timeouts, API errors) with backoff.
- Parser now falls back to HTML-to-text extraction when a message has no `text/plain` part.
- Telegram chunking uses a conservative safe payload limit for emoji-heavy text to reduce `MESSAGE_TOO_LONG` risk.
- Reduced log noise for idle polls (`no new messages`) by moving it to `DEBUG`.
- Added Docker `HEALTHCHECK`.
- Hub update script now notifies Telegram on pull/recreate failures and reports digest changes before container recreate.
- Added minimal unit tests (`parser`, `state`, `message_format`, `pipeline`) and CI workflow (`pytest` on push/PR).
- Pinned runtime dependencies in `requirements.txt`.

## [0.7.1] - 2026-04-17

### Changed

- Docker Hub build/push: single [`scripts/host_to_docker_hub.sh`](scripts/host_to_docker_hub.sh) (MINOR bump in bash, `.env` for `DOCKER_USER` / `TAG` / `NO_BUMP`); removed `docker-hub-build-push.sh`, `docker-hub-publish.sh`, and `bump_docker_minor.py`. `make hub-push` and docs updated accordingly.
- Docs: added [`docs/host-to-docker-hub.md`](docs/host-to-docker-hub.md) (usage for `host_to_docker_hub.sh`); removed redundant [`docs/docker-hub-build-and-vps-plan.md`](docs/docker-hub-build-and-vps-plan.md). [`DEPLOY.md`](DEPLOY.md) and cross-links point to the new guide.
- Hub deploy path: `vps-update-hub.sh`, `./scripts/host_to_vps.sh pull-up`, `make vps-pull`, and `deploy/email2telegram.service` now run `docker compose … up -d --force-recreate` after `pull` so the container is recreated from the new image. `DEPLOY.md` adds version-sync notes (local publish vs CI tag) and VPS verification commands (`/app/VERSION`, OCI label).
- **VPS from PC:** [`scripts/host_to_vps.sh`](scripts/host_to_vps.sh) replaces `scripts/vps.sh` (`sync`, `pull-up`, `enable-timer`, `deploy`, …); added [`docs/host-to-vps.md`](docs/host-to-vps.md). Earlier removals: `docker-hub-vps.sh`, `vps-sync-files.sh`.
- **Docs:** shorter `DEPLOY.md`, `docs/docker-hub-build-and-vps-plan.md`, README Docker sections; document VPS SSH `bash -lc` and `VPS_SSH_VERBOSE`.

## [0.4.1] - 2026-04-05

### Changed

- `VERSION` set to **0.4.1**.
- `DEPLOY.md`: Markdown/link formatting in the Hub deploy and periodic-pull sections; tighter list layout under “Get the new image onto the VPS”.
- `docs/docker-vps-architecture.md`: wider host-components table, spacing around Mermaid blocks, and normalized line endings (LF).

## [0.3.1] - 2026-04-05

### Added

- Semantic version in root `VERSION` (MAJOR.MINOR.PATCH) and runtime read via `src/version.py`.
- Code fingerprint at `.version/code_fingerprint` and script `scripts/bump_code_patch.py` to bump **PATCH** when `src/**/*.py` or `requirements.txt` change.
- Script `scripts/bump_docker_minor.py`; Docker Hub push path bumps **MINOR** before build (`scripts/docker-hub-build-push.sh`, `make hub-push`).
- Version banner before each outgoing Telegram message; `/start` and startup log include service version.
- `Dockerfile` copies `VERSION` and sets `org.opencontainers.image.version` via build-arg `APP_VERSION`.
- Email parsing: stable `dedup_key` from normalized `Message-ID` / `Message-Id`, or SHA-256 of raw RFC822 when absent; parsed output includes `message_id`.
- State store keeps a bounded list of delivered dedup keys so the same logical message is not posted twice if IMAP returns overlapping UIDs.
- GitHub Actions: Docker publish with **buildx** for **linux/amd64** and **linux/arm64**, passing `APP_VERSION` from `VERSION`.
- `scripts/docker-hub-publish.sh` for Docker Hub publish; `scripts/vps.sh` for PC→VPS sync and remote compose; `make hub-push` orchestrates local build and push.
- `deploy/vps-update-hub.sh`, `deploy/email2telegram-hub-update.service`, and `deploy/email2telegram-hub-update.timer` for periodic pull/restart from Hub on a VPS.
- `docs/docker-hub-build-and-vps-plan.md` — step-by-step Hub build and VPS update notes.

### Changed

- IMAP delivery pipeline: drops UIDs not after `last_seen_uid`, logs poll UID diagnostics, records dedup keys after successful Telegram delivery, and skips already-delivered keys while still advancing processed UIDs.
- `DEPLOY.md` expanded for Docker Hub, VPS updates, and timer-based refresh.
