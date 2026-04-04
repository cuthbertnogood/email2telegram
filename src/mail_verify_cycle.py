"""
Deprecated: единый конвейер в `main.py` (IMAP → опционально .eml → Telegram → \\Seen).

Сохранение писем: задайте в .env `EXPORT_MAIL_DIR=mail_export` и запускайте:

  python src/main.py
"""

from __future__ import annotations

import sys


def main() -> None:
    print(
        "mail_verify_cycle.py больше не используется.\n"
        "Запускайте: python src/main.py\n"
        "Для выгрузки .eml добавьте в .env: EXPORT_MAIL_DIR=mail_export",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
