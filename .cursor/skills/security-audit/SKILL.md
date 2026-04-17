---
name: security-audit
description: Audit email2telegram release artifacts for secret leaks and insecure defaults on GitHub, Docker Hub, and VPS. Use when preparing a release, reviewing .env/Dockerfile/compose/deploy scripts, changing scripts/release.sh, or when the user mentions security, secrets, leak, audit, hardening.
---

# Security Audit (email2telegram)

## Quick start

- Run repo/image secret scan: `.cursor/skills/security-audit/scripts/scan_secrets.sh`.
- Run image hardening checks: `.cursor/skills/security-audit/scripts/audit_image.sh`.
- Run VPS posture checks over SSH: `.cursor/skills/security-audit/scripts/audit_vps.sh`.
- For deep check including git history: `.cursor/skills/security-audit/scripts/scan_secrets.sh --history`.

## When to apply this skill

Apply this skill when task includes one of:

- release / publish / deploy flow updates;
- Docker Hub image push and rollout;
- edits in `.env*`, `Dockerfile`, `docker-compose*.yml`, `scripts/*.sh`, `deploy/*`;
- concerns about secret leakage, architecture hardening, or incident response.

## Non-negotiable invariants

1. Secrets MUST not be committed to git history (`.env`, tokens, private keys).
2. Secrets MUST not be copied into Docker image layers or image `Env`.
3. Container runtime MUST remain non-root unless explicitly justified.
4. VPS `.env` MUST be restricted (`chmod 600`) and not world-readable.
5. `TELEGRAM_CHAT_ID` MUST be inside `TELEGRAM_ALLOWED_CHAT_IDS`.
6. Release flow MUST fail-fast when security checks report `FAIL`.

## Surface checklists

### 1) Secrets

- Ensure `.env` is ignored by both git and docker build context.
- Scan tracked files and optional git history for token signatures.
- Inspect built image filesystem and config env for leaked credentials.
- Check logs and deploy scripts do not print sensitive env values.

### 2) Docker image

- Require non-root runtime user (`Config.User` is not empty/root).
- Require `HEALTHCHECK`.
- Warn on unusually large images and missing vulnerability scan tooling.
- Reject build practices that inject credentials through `ARG/ENV`.

### 3) GitHub

- Verify no secret-containing files are tracked.
- Verify no high-risk signatures in commits (optionally full history).
- Keep least privilege for PATs/workflows and avoid broad token scopes.
- Prefer branch protections and review gates before release merges.

### 4) VPS

- Check `.env` permissions and ownership under deploy directory.
- Check SSH baseline: `PasswordAuthentication no`, `PermitRootLogin no`.
- Verify container is healthy/running and exposes no unexpected ports.
- Validate deployed image tag matches expected release target.

## Architecture recommendations

- Keep secrets only in runtime `.env` on VPS; never in image or repo.
- Prefer private Docker Hub repo for production image.
- Use immutable tags (`vX.Y.Z`) in addition to `latest`.
- Rotate `TELEGRAM_BOT_TOKEN` and `IMAP_PASS` on schedule and incidents.
- Apply least privilege hardening in compose: `read_only`, `tmpfs`, `cap_drop`, `no-new-privileges`.

## Anti-patterns

- Committing `.env`, key files, or token-bearing logs.
- Using `COPY . .` Docker pattern that drags sensitive local files.
- Printing env values or raw secrets in shell trace/log output.
- Shipping with root container user when non-root is possible.

## Integration with release flow

- Default release should run secret scan before tests.
- Allow explicit emergency bypass only via `--skip-security`.
- Keep bypass visible in release output so operators can audit decisions.

## Additional resources

- Expanded procedures and remediation playbook: [reference.md](reference.md).
