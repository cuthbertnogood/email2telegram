"""
One-shot IMAP check: connect, optionally list folders, show mailbox status
and a short preview of the last few messages. No Telegram.

Run from project root:
  python src/imap_probe.py
  python src/imap_probe.py --list-folders
"""

from __future__ import annotations

import argparse
import imaplib
import os
import sys

from dotenv import load_dotenv

from parser import parse_email


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        print(f"Missing environment variable: {name}", file=sys.stderr)
        sys.exit(1)
    return value


def _imap_auth_hint(host: str) -> str:
    h = host.lower()
    lines = [
        "Common fixes (Yandex Mail):",
        "- Use the full address in E2T_IMAP_USER (e.g. you@yandex.ru, you@ya.ru, or your Yandex 360 domain).",
        "- In Yandex ID → Security, create a password for an external app and put it in E2T_IMAP_PASS (not your usual login if 2FA is on).",
        "- Try imap.yandex.com first; if login still fails, try imap.yandex.ru.",
        "- Regenerate the app password and paste again (no spaces; no trailing spaces in .env).",
    ]
    if "gmail" in h:
        lines.insert(
            0,
            "Host looks like Gmail: use imap.gmail.com + Google App Password if you meant Gmail, not Yandex.",
        )
    elif "outlook" in h or "office365" in h:
        lines.insert(
            0,
            "Host looks like Microsoft: OAuth is often required; this project expects Yandex IMAP by default.",
        )
    return "\n".join(lines)


def _connect() -> tuple[imaplib.IMAP4_SSL, str]:
    host = _required_env("E2T_IMAP_HOST")
    port = int(os.getenv("E2T_IMAP_PORT", "993"))
    user = _required_env("E2T_IMAP_USER")
    password = _required_env("E2T_IMAP_PASS")
    mailbox = os.getenv("E2T_IMAP_MAILBOX", "INBOX")

    client = imaplib.IMAP4_SSL(host, port)
    try:
        client.login(user, password)
    except imaplib.IMAP4.error as exc:
        print("IMAP login failed (server rejected username/password).", file=sys.stderr)
        print(f"  Host: {host!r}  User: {user!r}", file=sys.stderr)
        print(f"  Server said: {exc}", file=sys.stderr)
        print(_imap_auth_hint(host), file=sys.stderr)
        sys.exit(3)
    return client, mailbox


def cmd_list_folders(client: imaplib.IMAP4_SSL) -> None:
    typ, data = client.list()
    if typ != "OK" or not data:
        print("LIST failed.")
        return
    print("Folders (raw LIST):")
    for row in data:
        if isinstance(row, bytes):
            print(f"  {row.decode(errors='replace')}")
        else:
            print(f"  {row!r}")


def cmd_preview(client: imaplib.IMAP4_SSL, mailbox: str, last_n: int) -> None:
    typ, data = client.select(mailbox, readonly=True)
    if typ != "OK":
        print(f"Cannot select mailbox: {mailbox!r} ({typ})", file=sys.stderr)
        sys.exit(2)

    count_bytes = data[0] if data else b"0"
    try:
        count = int(count_bytes)
    except (TypeError, ValueError):
        count = 0

    print(f"Mailbox: {mailbox!r}")
    print(f"Messages (reported by server): {count}")

    if count == 0:
        print("No messages to preview.")
        return

    start_seq = max(1, count - last_n + 1)
    chunks: list[tuple[str, str, bytes]] = []
    for seq in range(start_seq, count + 1):
        typ, fetched = client.fetch(str(seq), "(UID RFC822)")
        if typ != "OK" or not fetched:
            continue
        uid = "?"
        raw: bytes | None = None
        for item in fetched:
            if not isinstance(item, tuple) or len(item) != 2:
                continue
            meta, payload = item
            if not isinstance(meta, bytes):
                continue
            if b"RFC822" not in meta:
                continue
            if isinstance(payload, (bytes, bytearray)):
                raw = bytes(payload)
            lo = meta.lower()
            if b"uid" in lo:
                parts = meta.split()
                for j, p in enumerate(parts):
                    if p.lower() == b"uid" and j + 1 < len(parts):
                        uid = parts[j + 1].decode(errors="replace")
                        break
            break
        if raw is not None:
            chunks.append((str(seq), uid, raw))

    if not chunks:
        print("FETCH returned no messages (unexpected).")
        return

    print(f"\nLast up to {last_n} message(s):\n")
    for seq, uid, raw in chunks:
        parsed = parse_email(raw)
        print(f"--- seq {seq}  UID {uid} ---")
        print(f"From:    {parsed.get('from', '')}")
        print(f"Subject: {parsed.get('subject', '')}")
        print(f"Date:    {parsed.get('date', '')}")
        body = (parsed.get("body") or "").replace("\r\n", "\n").strip()
        snippet = (body[:200] + "…") if len(body) > 200 else body
        print(f"Body:    {snippet or '(empty)'}")
        print()


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Test IMAP connection and mailbox.")
    parser.add_argument(
        "--list-folders",
        action="store_true",
        help="Print IMAP folder list (find correct mailbox name).",
    )
    parser.add_argument(
        "--last",
        type=int,
        default=3,
        metavar="N",
        help="Preview last N messages (default: 3).",
    )
    args = parser.parse_args()

    client, mailbox = _connect()
    try:
        if args.list_folders:
            cmd_list_folders(client)
            print()
        cmd_preview(client, mailbox, max(1, args.last))
    finally:
        try:
            client.close()
        except Exception:
            pass
        client.logout()

    print("IMAP check finished OK.")


if __name__ == "__main__":
    main()
