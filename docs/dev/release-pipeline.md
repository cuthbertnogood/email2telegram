# Release Pipeline

Primary entrypoint:

```bash
./scripts/release.sh
```

Pipeline steps:

1. Security scan (`.cursor/skills/security-audit/scripts/scan_secrets.sh`) unless skipped.
2. README sync check (`scripts/sync_readme_ru.py --check`).
3. Test run (`pytest -q`) unless skipped.
4. Build and publish Docker image to Docker Hub.
5. Verify image in registry.
6. Sync deploy files (`docker-compose.hub.yml`, `deploy/*`) to VPS.
7. Sync filtered `.env` to VPS — secrets/tokens rotation without SSH. Skip with `--skip-env-sync` or `VPS_SYNC_ENV=0`. See [deploy-to-vps.md](deploy-to-vps.md#env-sync-filtering-rules).
8. Pull and recreate container on VPS (`up -d --force-recreate`).
9. Optional timer enable on VPS (`--enable-timer`).
10. Push to GitHub (default on; skip with `--no-push-github`).

## Common Flags

- `--no-bump`
- `--skip-tests`
- `--skip-security`
- `--skip-env-sync`
- `--allow-dirty`
- `--enable-timer`
- `--no-push-github`
- `--tag <tag>`

## Rotating Secrets

Edit the new value in **local `.env`** (e.g. `TELEGRAM_BOT_TOKEN=...`), then run `./scripts/release.sh`. Step 7 pushes the filtered `.env` to VPS, step 8 recreates the container. No SSH, no manual VPS edit.

## Typical Runs

```bash
./scripts/release.sh
./scripts/release.sh --no-bump
./scripts/release.sh --skip-tests --no-push-github
./scripts/release.sh deploy@203.0.113.10 /opt/email2telegram
```
