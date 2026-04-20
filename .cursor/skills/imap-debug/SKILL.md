---
name: imap-debug
description: Debug IMAP connectivity and message previews with src/imap_probe.py (no Telegram). Use when troubleshooting IMAP auth, folders, or raw message shape before it hits parser/pipeline.
---

# IMAP debug (email2telegram)

## When to use

- Login failures, wrong mailbox, or need to inspect recent messages as the service would see them.
- Validating `.env` IMAP variables before running full `src/main.py`.

## Prerequisites

- Working `.env` with at least `IMAP_HOST`, `IMAP_USER`, `IMAP_PASS` (see `docs/user/env-reference.md` and `docs/user/yandex-imap.md`).

## Commands (repo root)

```bash
python src/imap_probe.py
python src/imap_probe.py --list-folders
python src/imap_probe.py --last 5
```

## Behavior

- Uses stdlib `imaplib` and `parser.parse_email` for previews — **does not** send Telegram traffic.
- Prints operator-oriented hints for common providers (Yandex/Gmail/Outlook) when auth fails.

## Escalation

- If probe works but pipeline fails, compare env vars used in `imap_client.py` vs probe (`IMAP_MAILBOX`, SSL port, etc.).
- For parsing bugs after fetch, reproduce with a saved `.eml` fixture in tests rather than live mailbox reads.
