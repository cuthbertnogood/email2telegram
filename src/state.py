from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


class StateStore:
    def __init__(self, path: str = ".state.json") -> None:
        self.path = Path(path)

    def get_last_seen_uid(self) -> Optional[int]:
        if not self.path.exists():
            return None
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            uid = raw.get("last_seen_uid")
            if uid is None:
                return None
            return int(uid)
        except (ValueError, json.JSONDecodeError, OSError):
            return None

    def set_last_seen_uid(self, uid: int) -> None:
        payload = {"last_seen_uid": int(uid)}
        self.path.write_text(json.dumps(payload), encoding="utf-8")
