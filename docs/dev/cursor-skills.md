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

## Usage Note

When working with the agent, reference the relevant skill explicitly so the matching conventions are applied consistently.
