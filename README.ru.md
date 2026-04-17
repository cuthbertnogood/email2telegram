# email2telegram (MVP)

[English](README.md) | Русский

Мост для доставки обновлений из почты Yandex по IMAP в Telegram. Приложение опрашивает IMAP, форматирует текст, отправляет его в Telegram и хранит состояние доставки.

Источник версии: [`VERSION`](VERSION). История релизов: [`CHANGELOG.md`](CHANGELOG.md).

## Быстрый старт (3 команды)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && cp .env.example .env
python src/main.py
```

Перед запуском задайте в `.env`: `IMAP_USER`, `IMAP_PASS`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_ALLOWED_CHAT_IDS`.

## Инструкции для пользователя

- Индекс: [`docs/user/README.md`](docs/user/README.md)
- Установка: [`docs/user/quickstart.md`](docs/user/quickstart.md)
- Yandex IMAP: [`docs/user/yandex-imap.md`](docs/user/yandex-imap.md)
- Telegram: [`docs/user/telegram-bot.md`](docs/user/telegram-bot.md)
- Деплой: [`docs/user/deploy.md`](docs/user/deploy.md)
- Переменные окружения: [`docs/user/env-reference.md`](docs/user/env-reference.md)
- Диагностика: [`docs/user/troubleshooting.md`](docs/user/troubleshooting.md)

## Документация проекта

- Индекс: [`docs/dev/README.md`](docs/dev/README.md)
- Релизный конвейер: [`docs/dev/release-pipeline.md`](docs/dev/release-pipeline.md)
- Публикация образа: [`docs/dev/publish-to-hub.md`](docs/dev/publish-to-hub.md)
- Выкатка на VPS: [`docs/dev/deploy-to-vps.md`](docs/dev/deploy-to-vps.md)
- Архитектура: [`docs/dev/architecture.md`](docs/dev/architecture.md)
- Версионирование: [`docs/dev/versioning.md`](docs/dev/versioning.md)
- CI: [`docs/dev/ci.md`](docs/dev/ci.md)
- Cursor skills: [`docs/dev/cursor-skills.md`](docs/dev/cursor-skills.md)

<!-- SYNC_EN_SHA256: 215ffa6a8a606c2e37fb383b551dc89a48c3e2b659953b2ceabbb26758520950 -->
