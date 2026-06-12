from __future__ import annotations

from imap_client import ImapClient


class FakeImap:
    def __init__(self, uid_map: dict[str, list[int]]) -> None:
        self.uid_map = uid_map
        self.last_search: str | None = None

    def uid(self, cmd: str, _charset, criteria: str):
        if cmd != "SEARCH":
            raise AssertionError(f"unexpected uid command: {cmd}")
        self.last_search = criteria
        uids = self.uid_map.get(criteria, [])
        return ("OK", [b" ".join(str(u).encode() for u in uids)])


def test_resolve_search_uids_unseen_only_no_cursor() -> None:
    client = ImapClient("h", 993, "u", "p")
    fake = FakeImap({"UNSEEN": [5, 10, 12]})
    assert client._resolve_search_uids(fake, None, unseen_only=True) == [5, 10, 12]
    assert fake.last_search == "UNSEEN"


def test_resolve_search_uids_unseen_only_with_cursor() -> None:
    client = ImapClient("h", 993, "u", "p")
    fake = FakeImap({"UNSEEN": [5, 10, 12]})
    assert client._resolve_search_uids(fake, 9, unseen_only=True) == [10, 12]


def test_resolve_search_uids_all_bootstrap() -> None:
    client = ImapClient("h", 993, "u", "p")
    fake = FakeImap({"ALL": [1, 2, 3]})
    assert client._resolve_search_uids(fake, None, unseen_only=False) == [1, 2, 3]
    assert fake.last_search == "ALL"


def test_resolve_search_uids_uid_range() -> None:
    client = ImapClient("h", 993, "u", "p")
    fake = FakeImap({"UID 11:4294967295": [11, 12]})
    assert client._resolve_search_uids(fake, 10, unseen_only=False) == [11, 12]
