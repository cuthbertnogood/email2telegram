# Security Audit Reference

## Release security checklist

Run in order before publish:

1. `.cursor/skills/security-audit/scripts/scan_secrets.sh`
2. `.cursor/skills/security-audit/scripts/audit_image.sh`
3. `.cursor/skills/security-audit/scripts/audit_vps.sh`

If any script returns non-zero, treat release as blocked.

## Secrets leak checklist

- `.env` and runtime state files are not tracked by git.
- `.env` is excluded from Docker build context.
- No token/key signatures in tracked files.
- No token/key signatures in git history (`--history` mode).
- Docker image does not contain `.env`, SSH keys, or sensitive files.
- Docker image config (`docker inspect`) does not expose secret env values.

## GitHub controls

- Keep repository visibility aligned to data sensitivity.
- Require reviews before merges to release branch.
- Keep PAT scopes minimal (avoid full `repo` when narrower scopes work).
- Rotate leaked credentials immediately and invalidate old tokens.

## Docker Hub controls

- Prefer private repository for production deployments.
- Push immutable tags (`vX.Y.Z`) in addition to mutable `latest`.
- Avoid passing credentials via build args or Dockerfile `ENV`.
- Use vulnerability scanner (`trivy`) and review HIGH/CRITICAL findings.

## VPS controls

- Deploy directory readable only by deploy user/group policy.
- `.env` must be mode `600`.
- SSH hardening: `PasswordAuthentication no`, `PermitRootLogin no`.
- Keep firewall minimal (usually SSH only for this service).
- Confirm `docker compose ... ps` reports running/healthy status.

## Credential rotation runbook

### Telegram bot token

1. Revoke old token in BotFather (`/revoke`).
2. Generate new token and update VPS `.env` `TELEGRAM_BOT_TOKEN`.
3. Restart service (`docker compose -f docker-compose.hub.yml up -d --force-recreate`).
4. Run smoke test (`/start` and test message delivery).

### IMAP app password

1. Revoke previous app password in provider security settings.
2. Generate new app password and update VPS `.env` `IMAP_PASS`.
3. Recreate container.
4. Verify polling and delivery in logs.

## Incident response baseline

When leak is suspected:

1. Stop releases.
2. Rotate exposed credentials.
3. Scan repo/history/image again.
4. Check Docker Hub tags and pull logs for unauthorized usage.
5. Audit VPS auth logs.
6. Resume release only after clean re-scan.

## Recommended hardening patch (optional)

For `docker-compose.hub.yml`, consider:

```yaml
services:
  email2telegram:
    read_only: true
    tmpfs:
      - /tmp
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
```

Apply only if runtime behavior remains intact (state already persists in `/data` volume).

## Review focus for this repository

- `scripts/release.sh`: security check runs by default, bypass explicit only.
- `scripts/host_to_vps.sh`: no secret echoing and safe SSH options.
- `Dockerfile`: non-root user and no secret-bearing copy patterns.
- `docker-compose.hub.yml`: least privilege where practical.
- `src/`: avoid logging raw environment values or sensitive content.
