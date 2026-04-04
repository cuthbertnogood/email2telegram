from __future__ import annotations


def parse_allowed_chat_ids(raw: str) -> frozenset[int]:
    """Comma- or semicolon-separated Telegram chat IDs (private user id or group id)."""
    s = raw.strip()
    if not s:
        raise RuntimeError("TELEGRAM_ALLOWED_CHAT_IDS is empty")
    out: set[int] = set()
    for part in s.replace(";", ",").split(","):
        p = part.strip()
        if not p:
            continue
        out.add(int(p))
    if not out:
        raise RuntimeError("TELEGRAM_ALLOWED_CHAT_IDS has no IDs")
    return frozenset(out)
