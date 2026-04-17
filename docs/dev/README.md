# Developer Documentation

This section covers release engineering and maintenance workflows.

## Documents

- [Release pipeline](release-pipeline.md)
- [Publish to Docker Hub](publish-to-hub.md)
- [Deploy to VPS](deploy-to-vps.md)
- [Architecture](architecture.md)
- [Versioning policy](versioning.md)
- [CI workflows](ci.md)
- [Cursor skills](cursor-skills.md)

## Local Setup For README Sync Guard

Install git hooks once:

```bash
./scripts/install_git_hooks.sh
```

This enables a pre-commit check that verifies `README.ru.md` is synced with `README.md`.
