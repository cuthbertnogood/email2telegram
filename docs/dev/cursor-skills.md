# Cursor Skills

Project-local skills live in `.cursor/skills/` and provide reusable playbooks for common tasks.

## Available Skills

- `telegram-bot-dev`
  - Use for Telegram handlers, JobQueue jobs, and delivery formatting changes.
  - Main scope: `src/main.py`, `src/telegram_client.py`, `src/pipeline.py`, `src/message_format.py`, `src/allowlist.py`.

- `cicd-pipeline`
  - Use for release/publish/deploy automation changes.
  - Main scope: `scripts/release.sh`, `scripts/host_to_docker_hub.sh`, `scripts/host_to_vps.sh`, deploy units.

- `security-audit`
  - Use for secret leak checks and hardening of release artifacts.
  - Includes helper scripts:
    - `.cursor/skills/security-audit/scripts/scan_secrets.sh`
    - `.cursor/skills/security-audit/scripts/audit_image.sh`
    - `.cursor/skills/security-audit/scripts/audit_vps.sh`

- `docs-ru-sync`
  - Use when changing `README.md` / `README.ru.md` or checking RU parity via `scripts/sync_readme_ru.py`.

- `pytest-local`
  - Use when running or extending tests under `tests/` (pytest layout, fakes, async markers).

- `imap-debug`
  - Use when diagnosing IMAP with `src/imap_probe.py` (no Telegram).

## MCP (Git)

- Workspace config: [.cursor/mcp.json](../../.cursor/mcp.json) registers **mcp-server-git** via `uvx` against `${workspaceFolder}`.
- Requires [uv](https://docs.astral.sh/uv/) / `uvx` on PATH. After editing MCP config, restart Cursor.
- Alternative (pip): `python3 -m mcp_server_git --repository .` — adjust `command`/`args` in `mcp.json` if you prefer this over `uvx`.

## Project hooks

- [.cursor/hooks.json](../../.cursor/hooks.json): `beforeShellExecution` runs [.cursor/hooks/shell_gate.py](../../.cursor/hooks/shell_gate.py) to prompt before commands touching `.env`, `release.sh`, `host_to_vps.sh`, or `git push --force`.

## Usage Note

When working with the agent, reference the relevant skill explicitly so the matching conventions are applied consistently.
