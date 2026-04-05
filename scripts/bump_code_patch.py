#!/usr/bin/env python3
"""Bump PATCH in VERSION when tracked code inputs change; maintain .version/code_fingerprint."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _code_paths(root: Path) -> list[Path]:
    src = root / "src"
    files: list[Path] = []
    if src.is_dir():
        files.extend(sorted(p for p in src.rglob("*.py") if p.is_file()))
    req = root / "requirements.txt"
    if req.is_file():
        files.append(req)
    return files


def _fingerprint(root: Path) -> str:
    h = hashlib.sha256()
    for path in _code_paths(root):
        rel = path.relative_to(root).as_posix().encode("utf-8")
        h.update(rel)
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def _parse_version(raw: str) -> tuple[int, int, int]:
    parts = raw.strip().split(".")
    if len(parts) != 3:
        raise ValueError(f"Expected MAJOR.MINOR.PATCH, got: {raw!r}")
    return int(parts[0]), int(parts[1]), int(parts[2])


def _write_version(root: Path, major: int, minor: int, patch: int) -> None:
    (root / "VERSION").write_text(f"{major}.{minor}.{patch}\n", encoding="utf-8")


def main() -> int:
    root = _repo_root()
    fp_path = root / ".version" / "code_fingerprint"
    digest = _fingerprint(root)

    if not fp_path.is_file():
        fp_path.parent.mkdir(parents=True, exist_ok=True)
        fp_path.write_text(digest + "\n", encoding="utf-8")
        print("Initialized .version/code_fingerprint (no PATCH bump).")
        return 0

    old = fp_path.read_text(encoding="utf-8").strip()
    if old == digest:
        print("Code fingerprint unchanged; VERSION not modified.")
        return 0

    ver_raw = (root / "VERSION").read_text(encoding="utf-8")
    major, minor, patch = _parse_version(ver_raw)
    patch += 1
    _write_version(root, major, minor, patch)
    fp_path.write_text(digest + "\n", encoding="utf-8")
    print(f"Code changed: PATCH bumped → {major}.{minor}.{patch}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        raise SystemExit(1) from e
