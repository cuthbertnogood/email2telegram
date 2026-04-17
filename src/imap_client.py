from __future__ import annotations

import imaplib
import threading
import time
from contextlib import contextmanager
from typing import Iterator, List, Tuple

# Some IMAP servers mis-handle UID ranges with `*` in UID SEARCH (e.g. `UID 8:*`
# matching lower UIDs). Use an explicit upper bound (RFC 3501 UID is 32-bit).
_IMAP_UID_MAX = 4_294_967_295
_IMAP_CONNECT_ATTEMPTS = 3
_IMAP_CONNECT_BACKOFF_SECONDS = 1.5


class ImapClient:
    def __init__(self, host: str, port: int, user: str, password: str, mailbox: str = "INBOX") -> None:
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.mailbox = mailbox
        self._client: imaplib.IMAP4_SSL | None = None
        self._lock = threading.Lock()

    def _open_connection(self) -> imaplib.IMAP4_SSL:
        client: imaplib.IMAP4_SSL | None = None
        last_error: Exception | None = None
        for attempt in range(1, _IMAP_CONNECT_ATTEMPTS + 1):
            try:
                client = imaplib.IMAP4_SSL(self.host, self.port)
                client.login(self.user, self.password)
                status, _ = client.select(self.mailbox)
                if status != "OK":
                    raise RuntimeError(f"Cannot select mailbox: {self.mailbox}")
                return client
            except Exception as exc:
                last_error = exc
                if client is not None:
                    try:
                        client.logout()
                    except Exception:
                        pass
                client = None
                if attempt < _IMAP_CONNECT_ATTEMPTS:
                    time.sleep(_IMAP_CONNECT_BACKOFF_SECONDS * attempt)
                    continue
                raise RuntimeError(
                    f"IMAP connect/login/select failed after {_IMAP_CONNECT_ATTEMPTS} attempts"
                ) from last_error
        raise RuntimeError("IMAP client initialization failed")

    @contextmanager
    def connection(self) -> Iterator[imaplib.IMAP4_SSL]:
        with self._lock:
            if self._client is None:
                self._client = self._open_connection()
            try:
                yield self._client
            except Exception:
                if self._client is not None:
                    try:
                        self._client.logout()
                    except Exception:
                        pass
                self._client = None
                raise

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
            status_fetch, fetched = client.uid("FETCH", uid_raw, "(BODY.PEEK[])")
            if status_fetch != "OK" or not fetched:
                continue
            raw = fetched[0][1]
            if isinstance(raw, (bytes, bytearray)):
                messages.append((uid, bytes(raw)))
        return messages

    def fetch_new_messages(self, last_seen_uid: int | None) -> List[Tuple[int, bytes]]:
        with self.connection() as client:
            return self._search_and_fetch_rfc822(client, last_seen_uid)

    def fetch_new_messages_in_connection(
        self, client: imaplib.IMAP4_SSL, last_seen_uid: int | None
    ) -> List[Tuple[int, bytes]]:
        return self._search_and_fetch_rfc822(client, last_seen_uid)

    def mark_uids_seen_in_connection(self, client: imaplib.IMAP4_SSL, uids: List[int]) -> None:
        if not uids:
            return
        uid_set = ",".join(str(uid) for uid in sorted(set(uids)))
        st, _ = client.uid("STORE", uid_set, "+FLAGS.SILENT", r"(\Seen)")
        if st != "OK":
            raise RuntimeError(f"IMAP STORE \\Seen failed for UIDs {uid_set}")

    def mark_uids_seen(self, uids: List[int]) -> None:
        with self.connection() as client:
            self.mark_uids_seen_in_connection(client, uids)
