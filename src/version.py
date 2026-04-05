from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_version() -> str:
    path = project_root() / "VERSION"
    if not path.is_file():
        raise RuntimeError("Missing VERSION file at project root.")
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        raise RuntimeError("VERSION file is empty.")
    return raw


def telegram_version_banner(version: str) -> str:
    return f"[email2telegram v{version}]"
