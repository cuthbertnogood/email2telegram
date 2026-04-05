from __future__ import annotations

import hashlib
from email import message_from_bytes
from email.header import decode_header, make_header
from email.message import Message
from typing import Dict


def _dedup_key(raw_message: bytes, msg: Message) -> str:
    """Stable key: normalized Message-ID, else SHA-256 of raw RFC822 bytes."""
    mid_raw = msg.get("Message-ID") or msg.get("Message-Id") or ""
    inner = (mid_raw or "").strip()
    if len(inner) >= 2 and inner.startswith("<") and inner.endswith(">"):
        inner = inner[1:-1].strip()
    if inner:
        return f"mid:{inner}"
    return f"raw:{hashlib.sha256(raw_message).hexdigest()}"


def _decode_header_value(value: str | None) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def _extract_text_body(message: Message) -> str:
    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", "")).lower()
            if content_type == "text/plain" and "attachment" not in content_disposition:
                charset = part.get_content_charset() or "utf-8"
                payload = part.get_payload(decode=True) or b""
                try:
                    return payload.decode(charset, errors="replace")
                except LookupError:
                    return payload.decode("utf-8", errors="replace")
        return ""

    charset = message.get_content_charset() or "utf-8"
    payload = message.get_payload(decode=True) or b""
    try:
        return payload.decode(charset, errors="replace")
    except LookupError:
        return payload.decode("utf-8", errors="replace")


def parse_email(raw_message: bytes) -> Dict[str, str]:
    msg = message_from_bytes(raw_message)
    body = _extract_text_body(msg).strip()
    mid_raw = msg.get("Message-ID") or msg.get("Message-Id") or ""
    return {
        "from": _decode_header_value(msg.get("From")),
        "subject": _decode_header_value(msg.get("Subject")),
        "date": _decode_header_value(msg.get("Date")),
        "message_id": (mid_raw or "").strip(),
        "dedup_key": _dedup_key(raw_message, msg),
        "body": body,
    }
