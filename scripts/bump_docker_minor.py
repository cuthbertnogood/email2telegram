#!/usr/bin/env python3
"""Increment MINOR in VERSION (for Docker Hub build+push flow)."""

from __future__ import annotations

import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _parse_version(raw: str) -> tuple[int, int, int]:
    parts = raw.strip().split(".")
    if len(parts) != 3:
        raise ValueError(f"Expected MAJOR.MINOR.PATCH, got: {raw!r}")
    return int(parts[0]), int(parts[1]), int(parts[2])


def main() -> int:
    root = _repo_root()
    path = root / "VERSION"
    major, minor, patch = _parse_version(path.read_text(encoding="utf-8"))
    minor += 1
    path.write_text(f"{major}.{minor}.{patch}\n", encoding="utf-8")
    print(f"MINOR bumped for Docker Hub build → {major}.{minor}.{patch}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        raise SystemExit(1) from e
