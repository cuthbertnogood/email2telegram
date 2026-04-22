# Versioning Policy

The project uses `MAJOR.MINOR.PATCH` in the root `VERSION` file.

- `PATCH`: bump after code changes in `src/` or `requirements.txt` using:

```bash
python3 scripts/bump_code_patch.py
```

- `PATCH` (image releases): by default bumped by `scripts/host_to_docker_hub.sh` before each Docker Hub build (e.g. `0.16.4` → `0.16.5`). Disable with `NO_BUMP=1` or `--no-bump` when `VERSION` was already set manually. To bump `MINOR` or `MAJOR`, edit `VERSION` by hand, then build with `NO_BUMP=1`.

Runtime behavior:

- App version is included in outgoing Telegram messages.
- Startup notification reports version change when state volume is reused.
