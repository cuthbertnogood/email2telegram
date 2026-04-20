# Контекст агента (email2telegram)

## Язык

- Отвечай пользователю **по-русски** (кратко и по делу).
- **Код**, идентификаторы, **коммиты**, комментарии в коде — **по-английски**.

Подробнее: [.cursor/rules/09-communication.mdc](.cursor/rules/09-communication.mdc).

## Что это за репозиторий

Мост IMAP → Telegram (MVP): опрос почты, опционально сохранение `.eml`, отправка текста в Telegram. Python 3.12+, код приложения в `src/`.

## Запуск

- Сервис: `python src/main.py` (из корня репозитория; импорты без префикса `src.`).
- Только IMAP (без Telegram): `python src/imap_probe.py`
- Лог в файл: `./scripts/run-with-log.sh python src/main.py` → `logs/last-run.log`
- Тесты: `python3 -m pytest -q`

Детали: [.cursor/rules/01-core.mdc](.cursor/rules/01-core.mdc), [.cursor/rules/05-tests.mdc](.cursor/rules/05-tests.mdc).

## Конфигурация

- Скопировать `.env.example` → `.env`. **Не коммитить** `.env`.
- Справка по переменным: [docs/user/env-reference.md](docs/user/env-reference.md).

## Не трогать по своей инициативе

- `scripts/host_to_vps.sh`, `scripts/release.sh` — менять **только по явной просьбе** пользователя (деплой / релизный пайплайн).
- После правок в `scripts/release.sh`, `Dockerfile`, `docker-compose*.yml`, `deploy/**` — из корня репозитория запустить `./.cursor/skills/security-audit/scripts/scan_secrets.sh` перед публикацией/коммитом.

Подробнее: [.cursor/rules/10-secrets.mdc](.cursor/rules/10-secrets.mdc).

- Хост VPS, пользователь, учётные данные для окружения — в **пользовательских Memories** Cursor, не в репозитории.

## Куда смотреть

- Карта модулей: [docs/dev/architecture.md](docs/dev/architecture.md)
- Деплой: [DEPLOY.md](DEPLOY.md), [docs/user/deploy.md](docs/user/deploy.md), [docs/dev/deploy-to-vps.md](docs/dev/deploy-to-vps.md)
- Перед крупными архитектурными изменениями — решения в `.cursor/plans/*.plan.md`: [.cursor/rules/11-plans.mdc](.cursor/rules/11-plans.mdc)

## Секреты

- Не логировать и не вставлять в чат: содержимое `.env`, пароль IMAP, токен бота, полные тела писем.

Полный чеклист: [.cursor/rules/10-secrets.mdc](.cursor/rules/10-secrets.mdc).
