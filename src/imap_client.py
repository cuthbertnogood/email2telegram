from __future__ import annotations

import imaplib
from typing import List, Tuple


class ImapClient:
    def __init__(self, host: str, port: int, user: str, password: str, mailbox: str = "INBOX") -> None:
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.mailbox = mailbox

    def _connect(self) -> imaplib.IMAP4_SSL:
        client = imaplib.IMAP4_SSL(self.host, self.port)
        client.login(self.user, self.password)
        status, _ = client.select(self.mailbox)
        if status != "OK":
            raise RuntimeError(f"Cannot select mailbox: {self.mailbox}")
        return client

    def fetch_new_messages(self, last_seen_uid: int | None) -> List[Tuple[int, bytes]]:
        client = self._connect()
        try:
            if last_seen_uid is None:
                criteria = "ALL"
            else:
                criteria = f"UID {last_seen_uid + 1}:*"

            status, data = client.uid("SEARCH", None, criteria)
            if status != "OK":
                return []

            uid_bytes = (data[0] or b"").split()
            messages: List[Tuple[int, bytes]] = []
            for uid_raw in uid_bytes:
                uid = int(uid_raw)
                status_fetch, fetched = client.uid("FETCH", uid_raw, "(RFC822)")
                if status_fetch != "OK" or not fetched:
                    continue
                # Typical fetch response: [(b'123 (RFC822 {N}', b'...raw bytes...'), b')']
                raw = fetched[0][1]
                if isinstance(raw, (bytes, bytearray)):
                    messages.append((uid, bytes(raw)))
            return messages
        finally:
            try:
                client.close()
            except Exception:
                pass
            client.logout()
