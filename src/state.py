from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

_MAX_MESSAGE_IDS = 500


class StateStore:
    def __init__(self, path: str = ".state.json") -> None:
        self.path = Path(path)

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            return raw if isinstance(raw, dict) else {}
        except (json.JSONDecodeError, OSError, TypeError):
            return {}

    def _save(self, data: dict[str, Any]) -> None:
        payload = json.dumps(data, ensure_ascii=False)
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp_path.write_text(payload, encoding="utf-8")
        os.replace(tmp_path, self.path)

    def get_last_seen_uid(self) -> Optional[int]:
        data = self._load()
        uid = data.get("last_seen_uid")
        if uid is None:
            return None
        try:
            return int(uid)
        except (TypeError, ValueError):
            return None

    def set_last_seen_uid(self, uid: int) -> None:
        data = self._load()
        data["last_seen_uid"] = int(uid)
        self._save(data)

    def get_last_service_version(self) -> Optional[str]:
        data = self._load()
        raw = data.get("last_service_version")
        if raw is None:
            return None
        value = str(raw).strip()
        return value or None

    def set_last_service_version(self, version: str) -> None:
        value = (version or "").strip()
        if not value:
            return
        data = self._load()
        data["last_service_version"] = value
        self._save(data)

    def has_message_id(self, message_id: str) -> bool:
        mid = (message_id or "").strip()
        if not mid:
            return False
        ids = self._load().get("delivered_message_ids")
        if not isinstance(ids, list):
            return False
        return mid in ids

    def add_message_id(self, message_id: str) -> None:
        mid = (message_id or "").strip()
        if not mid:
            return
        data = self._load()
        ids = list(data.get("delivered_message_ids") or [])
        if not isinstance(ids, list):
            ids = []
        if mid in ids:
            return
        ids.append(mid)
        data["delivered_message_ids"] = ids[-_MAX_MESSAGE_IDS:]
        self._save(data)
