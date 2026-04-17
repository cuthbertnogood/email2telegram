# Release Pipeline

Primary entrypoint:

```bash
./scripts/release.sh
```

Pipeline steps:

1. Optional README sync check (`scripts/sync_readme_ru.py --check`).
2. Test run (`pytest -q`) unless skipped.
3. Build and publish Docker image to Docker Hub.
4. Sync deploy files to VPS.
5. Pull and recreate container on VPS.
6. Optional timer enable on VPS.
7. Optional push to GitHub (enabled by default).

## Common Flags

- `--no-bump`
- `--skip-tests`
- `--allow-dirty`
- `--enable-timer`
- `--no-push-github`
- `--tag <tag>`

## Typical Runs

```bash
./scripts/release.sh
./scripts/release.sh --no-bump
./scripts/release.sh --skip-tests --no-push-github
./scripts/release.sh deploy@203.0.113.10 /opt/email2telegram
```
