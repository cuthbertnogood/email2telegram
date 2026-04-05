from __future__ import annotations

import imaplib
from contextlib import contextmanager
from typing import Iterator, List, Tuple

# Some IMAP servers mis-handle UID ranges with `*` in UID SEARCH (e.g. `UID 8:*`
# matching lower UIDs). Use an explicit upper bound (RFC 3501 UID is 32-bit).
_IMAP_UID_MAX = 4_294_967_295


class ImapClient:
    def __init__(self, host: str, port: int, user: str, password: str, mailbox: str = "INBOX") -> None:
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.mailbox = mailbox

    @contextmanager
    def connection(self) -> Iterator[imaplib.IMAP4_SSL]:
        client = imaplib.IMAP4_SSL(self.host, self.port)
        client.login(self.user, self.password)
        status, _ = client.select(self.mailbox)
        if status != "OK":
            try:
                client.logout()
            except Exception:
                pass
            raise RuntimeError(f"Cannot select mailbox: {self.mailbox}")
        try:
            yield client
        finally:
            try:
                client.close()
            except Exception:
                pass
            client.logout()

    def _search_and_fetch_rfc822(
        self, client: imaplib.IMAP4_SSL, last_seen_uid: int | None
    ) -> List[Tuple[int, bytes]]:
        if last_seen_uid is None:
            criteria = "ALL"
        else:
            lo = last_seen_uid + 1
            criteria = f"UID {lo}:{_IMAP_UID_MAX}"

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
            raw = fetched[0][1]
            if isinstance(raw, (bytes, bytearray)):
                messages.append((uid, bytes(raw)))
        return messages

    def fetch_new_messages(self, last_seen_uid: int | None) -> List[Tuple[int, bytes]]:
        with self.connection() as client:
            return self._search_and_fetch_rfc822(client, last_seen_uid)

    def mark_uids_seen(self, uids: List[int]) -> None:
        if not uids:
            return
        with self.connection() as client:
            for uid in uids:
                st, _ = client.uid("STORE", str(uid), "+FLAGS.SILENT", r"(\Seen)")
                if st != "OK":
                    raise RuntimeError(f"IMAP STORE \\Seen failed for UID {uid}")
