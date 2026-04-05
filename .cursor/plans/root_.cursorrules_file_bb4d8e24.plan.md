---
name: Root .cursorrules file
overview: Добавить в корень репозитория файл `.cursorrules` с кратким описанием стека и ссылкой на существующие правила в `.cursor/rules/`, чтобы агенты и совместимость со старым форматом Cursor были покрыты без дублирования длинного текста про терминал.
todos:
  - id: add-cursorrules
    content: Создать `.cursorrules` в корне с кратким контекстом проекта и ссылкой на `.cursor/rules/`
    status: completed
isProject: false
---

# Файл `.cursorrules` в корне проекта

## Контекст

- Репозиторий: [email2telegram](README.md) — Python-мост IMAP (Yandex и др.) → Telegram, точка входа `src/main.py`, конфиг через `.env` по [`.env.example`](.env.example).
- Уже подключено правило Cursor: [`.cursor/rules/share-terminal-output.mdc`](.cursor/rules/share-terminal-output.mdc) с `alwaysApply: true` (как передавать вывод терминала агенту).

## Что сделать

1. **Создать** [`/Users/cuthbert/work/cursor/email2telegram/.cursorrules`](/Users/cuthbert/work/cursor/email2telegram/.cursorrules) (один файл в корне, без вложенных папок).

2. **Содержимое** (предлагаемая структура, на русском — в духе существующего правила):

   - Кратко: назначение проекта, Python 3.12+, основные пути (`src/`, `scripts/run-with-log.sh`, опционально `mail_export/` для `.eml`).
   - Рабочие команды по [README](README.md): venv, `pip install -r requirements.txt`, `python src/imap_probe.py`, `python src/main.py`.
   - Безопасность: не коммитить `.env`, секреты только в env.
   - Явная отсылка: **дополнительные и обязательные инструкции** — в [`.cursor/rules/`](.cursor/rules/); про вывод терминала — см. `share-terminal-output.mdc` (без копирования всего текста, чтобы не расходиться при правках).

3. **Не трогать** существующие `.mdc`, если вы не попросите объединить или перенести текст в один файл.

## Примечание по экосистеме Cursor

Корневой `.cursorrules` — устаревший, но всё ещё поддерживаемый способ; параллельно с ним продолжают работать правила из [`.cursor/rules/*.mdc`](.cursor/rules/). Имеет смысл держать в `.cursorrules` только то, что должно быть «на виду» в корне, а детали — в `rules/`.
