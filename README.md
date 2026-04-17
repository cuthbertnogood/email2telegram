# email2telegram (MVP)

English | [Русский](README.ru.md)

Bridge Yandex IMAP mailbox updates to Telegram chat delivery. The app polls IMAP, formats text, forwards to Telegram, and persists delivery state.

Version source: [`VERSION`](VERSION). Release history: [`CHANGELOG.md`](CHANGELOG.md).

## 3-Command Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && cp .env.example .env
python src/main.py
```

Before run, set in `.env`: `IMAP_USER`, `IMAP_PASS`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_ALLOWED_CHAT_IDS`.

## User Documentation

- Index: [`docs/user/README.md`](docs/user/README.md)
- Setup: [`docs/user/quickstart.md`](docs/user/quickstart.md)
- Yandex IMAP: [`docs/user/yandex-imap.md`](docs/user/yandex-imap.md)
- Telegram: [`docs/user/telegram-bot.md`](docs/user/telegram-bot.md)
- Deploy: [`docs/user/deploy.md`](docs/user/deploy.md)
- Env vars: [`docs/user/env-reference.md`](docs/user/env-reference.md)
- Troubleshooting: [`docs/user/troubleshooting.md`](docs/user/troubleshooting.md)

## Project Documentation

- Index: [`docs/dev/README.md`](docs/dev/README.md)
- Release pipeline: [`docs/dev/release-pipeline.md`](docs/dev/release-pipeline.md)
- Publish image: [`docs/dev/publish-to-hub.md`](docs/dev/publish-to-hub.md)
- VPS rollout: [`docs/dev/deploy-to-vps.md`](docs/dev/deploy-to-vps.md)
- Architecture: [`docs/dev/architecture.md`](docs/dev/architecture.md)
- Versioning: [`docs/dev/versioning.md`](docs/dev/versioning.md)
- CI: [`docs/dev/ci.md`](docs/dev/ci.md)
- Cursor skills: [`docs/dev/cursor-skills.md`](docs/dev/cursor-skills.md)
