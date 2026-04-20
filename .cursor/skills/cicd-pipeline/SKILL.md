---
name: cicd-pipeline
description: Build and operate the email2telegram CI/CD release pipeline. Use when the user asks about release, ci/cd, Docker Hub publishing, VPS deploy, image rollout, or one-shot shipping from PC.
---

# CI/CD Pipeline (email2telegram)

## Quick start

- Primary release entrypoint: `./scripts/release.sh`.
- This one command runs tests, publishes the Docker image, syncs deploy files to VPS, pushes a filtered `.env` to VPS (for secret/token rotation without SSH), triggers remote `pull + up -d --force-recreate`, and pushes local project changes to GitHub by default.
- Use low-level scripts only for partial/manual steps:
  - `./scripts/host_to_docker_hub.sh`
  - `./scripts/host_to_vps.sh` (`sync`, `sync-env`, `pull-up`, `enable-timer`, `deploy`)

## When to apply this skill

Apply this skill when task mentions one of:

- release / ship / publish image;
- CI/CD pipeline changes;
- Docker Hub push flow;
- VPS deploy or rollout automation;
- combining build and deploy into one script.

## Canonical release flow

1. Ensure `.env` has `DOCKER_USER`, `VPS_USER`, `VPS_HOST` (and optional VPS SSH vars).
2. Run `./scripts/release.sh` (use `--no-push-github` when GitHub push must be skipped).
3. Verify on VPS:
   - `docker compose -f docker-compose.hub.yml ps`
   - `docker compose -f docker-compose.hub.yml logs -f`

## Supported release modes

- Default: `./scripts/release.sh` (tests + MINOR bump + Docker push + VPS deploy + VPS `.env` sync + GitHub push).
- No bump: `./scripts/release.sh --no-bump`.
- Hotfix skip tests: `./scripts/release.sh --skip-tests`.
- Skip VPS `.env` push (manual secret management): `./scripts/release.sh --skip-env-sync` or `VPS_SYNC_ENV=0` in `.env`.
- Include timer setup: `./scripts/release.sh --enable-timer`.
- Skip GitHub push: `./scripts/release.sh --no-push-github`.
- Override target host/dir: `./scripts/release.sh user@host /opt/email2telegram`.

## Secret rotation

When `TELEGRAM_BOT_TOKEN`, `IMAP_PASS`, or similar secrets need rotation: edit local `.env` on PC, run `./scripts/release.sh`. Filtered `.env` (no `DOCKER_USER`/`VPS_*`/`LLM_*`) is pushed to VPS and container is force-recreated. No SSH, no manual VPS edit.

## Required files in this repo

- `scripts/release.sh` - one-shot release wrapper.
- `scripts/host_to_docker_hub.sh` - buildx + Docker Hub push + MINOR bump policy.
- `scripts/host_to_vps.sh` - sync/pull-up/enable-timer commands.
- `scripts/host_to_github.sh` - stage/commit/push current branch to GitHub.
- `deploy/vps-update-hub.sh` - VPS-side pull + recreate script.
- `deploy/email2telegram-hub-update.service`
- `deploy/email2telegram-hub-update.timer`
- `docker-compose.hub.yml`

## Safety rules

- Do not print tokens/passwords from `.env`.
- Keep fail-fast behavior (`set -euo pipefail`) in shell scripts.
- Run tests before publishing unless user explicitly skips.
- Keep deploy idempotent (`pull` + `up -d --force-recreate`).
- Treat timer as fallback, not main release trigger.
