# email2telegram (MVP)

[English](README.md) | Русский

Простой мост: **подключение почтового ящика Yandex** по IMAP, опрос новых писем и пересылка текста в чат Telegram. (Другие IMAP-серверы подойдут, если задать `IMAP_HOST` вручную.)

**Версия:** см. файл [`VERSION`](VERSION) в корне репозитория. История изменений: [`CHANGELOG.md`](CHANGELOG.md). Каждое исходящее сообщение в Telegram начинается с версии запущенного сервиса.

- После правок в `src/` или в `requirements.txt` выполните `python3 scripts/bump_code_patch.py`, чтобы поднять **PATCH** и обновить отпечаток (коммитьте `VERSION` и `.version/code_fingerprint` вместе с изменениями).
- Каждая публикация образа в **Docker Hub** через **`./scripts/docker-hub-publish.sh`** (или `make hub-push` / `./scripts/docker-hub-vps.sh hub-build-push` — тот же сценарий) перед сборкой поднимает **MINOR**; после публикации закоммитьте обновлённый `VERSION`.

## Возможности (MVP)

- Подключение к ящику **Yandex** по IMAP (`imap.yandex.com` / `imap.yandex.ru`).
- **Один конвейер:** забрать новые письма → опционально сохранить как `.eml` → отправить **весь текст письма** в Telegram (при превышении лимита Telegram — несколькими сообщениями) → пометить как **прочитанные** на сервере → обновить `last_seen_uid`.
- Опрос IMAP каждые N секунд.
- Без фильтров (все новые письма из выбранной папки).
- Форматирование текста для Telegram — в `src/message_format.py` (позже можно сменить, например на Markdown).
- **Список разрешённых чатов:** `TELEGRAM_ALLOWED_CHAT_IDS` — почта уходит только в `TELEGRAM_CHAT_ID`, если он входит в список; команда `/start` обрабатывается только для чатов из списка (остальные пользователи не получают ответов).
- Хранение `last_seen_uid` в файле состояния, чтобы после перезапуска старые письма не пересылались повторно.

## Docker (VPS)

Кратко:

```bash
cp .env.example .env   # заполните и chmod 600 .env
docker compose up -d --build
docker compose logs -f
```

Полный чеклист (файрвол, systemd, бэкапы, **Docker Hub**): см. **[DEPLOY.md](DEPLOY.md)**.

В Compose заданы `STATE_FILE=/data/.state.json` и опционально `TZ`. Чтобы сохранять `.eml` на диск, добавьте в `.env` строку `EXPORT_MAIL_DIR=/data/mail_export`. Логи контейнера ротируются (10 МБ × 3 файла). Именованный том `email2telegram_data` сохраняет состояние между перезапусками.

## Требования

- Python 3.12+
- Учётные данные Yandex Mail (или совместимого IMAP)
- Токен Telegram-бота и ID чата

## Установка и запуск

1. Зависимости:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Файл окружения:

   ```bash
   cp .env.example .env
   ```

3. Скопируйте `.env.example` в `.env` и задайте **`IMAP_USER`** / **`IMAP_PASS`**, **`TELEGRAM_BOT_TOKEN`**, **`TELEGRAM_CHAT_ID`** и **`TELEGRAM_ALLOWED_CHAT_IDS`** (в личке с ботом обычно тот же числовой id, что и `TELEGRAM_CHAT_ID`; несколько id — через запятую).

### Yandex Mail (IMAP)

- Откройте [Yandex ID → Безопасность](https://id.yandex.ru/security) для того же аккаунта, что и почта.
- Создайте **пароль для внешнего приложения** («Пароли приложений» / «Пароль для приложения»). Укажите его в **`IMAP_PASS`**.
- **`IMAP_USER`**: полный адрес — `name@yandex.ru`, `name@yandex.com`, `name@ya.ru` или домен на Yandex 360.
- **`IMAP_HOST=imap.yandex.com`**, **`IMAP_PORT=993`**. Если вход не проходит, попробуйте **`imap.yandex.ru`**.
- В настройках почты Yandex включите доступ для **почтовых клиентов** / IMAP, если такая опция есть.

4. **Проверка IMAP (без Telegram):**

   ```bash
   python src/imap_probe.py
   ```

   Если письма в другой папке (не `INBOX`), выведите список папок и задайте `IMAP_MAILBOX` в `.env`:

   ```bash
   python src/imap_probe.py --list-folders
   ```

   Опционально: просмотр нескольких последних писем — `python src/imap_probe.py --last 5`.

5. Полный мост (нужны переменные Telegram в `.env`):

   ```bash
   python src/main.py
   ```

### Если видите `AUTHENTICATIONFAILED` / неверные учётные данные

Сервер отклонил `IMAP_USER` / `IMAP_PASS`. Для Yandex проверьте:

- **Пароль приложения**: при двухфакторной аутентификации нужен [пароль для приложения](https://yandex.ru/support/id/authorization/app-passwords.html), а не пароль от входа в браузере.
- **Полный логин**: `IMAP_USER` — целиком адрес электронной почты.
- **Хост**: `imap.yandex.com` или `imap.yandex.ru`.
- **`.env`**: без лишних пробелов; кавычки — только если в значении есть пробелы.
- **venv**: после `source .venv/bin/activate` команда `which python` должна указывать внутрь `.venv/`. Иначе пересоздайте окружение: `rm -rf .venv && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.

## Переменные окружения

- `IMAP_HOST` (обязательно)
- `IMAP_PORT` (по умолчанию `993`)
- `IMAP_USER` (обязательно)
- `IMAP_PASS` (обязательно)
- `IMAP_MAILBOX` (по умолчанию `INBOX`)
- `POLL_INTERVAL_SECONDS` (по умолчанию `45`)
- `TELEGRAM_BOT_TOKEN` (обязательно)
- `TELEGRAM_ALLOWED_CHAT_IDS` (обязательно) — список ID чатов, которым разрешена доставка почты и `/start`; должен включать `TELEGRAM_CHAT_ID`.
- `TELEGRAM_CHAT_ID` (обязательно) — чат, куда пересылается почта (должен быть в списке разрешённых).
- `EXPORT_MAIL_DIR` (опционально) — если задано, каждое доставленное письмо также пишется как `{uid}.eml` в этот каталог.
- `STATE_FILE` (опционально, по умолчанию `.state.json`) — путь к файлу курсора UID; в Docker используйте `/data/.state.json`.

## Ручная проверка

1. Отправьте тестовое письмо на настроенный ящик.
2. Проверьте Telegram: каждое сообщение начинается с `[email2telegram v…]`; далее заголовки и тело (длинное тело может прийти частями с номерами `1/n`).
3. Перезапустите сервис и убедитесь, что уже пересланные письма не отправляются снова.
4. Отправьте письмо с темой/телом в UTF-8 и убедитесь, что текст декодируется корректно.
