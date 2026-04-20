#!/usr/bin/env python3
"""Cursor beforeShellExecution hook: ask user to confirm risky shell commands."""

from __future__ import annotations

import json
import re
import sys


def _reasons(command: str) -> list[str]:
    reasons: list[str] = []
    # .env files (not .env.example)
    if re.search(r"(?:^|[\s/'\"])\.env(?!\.example\b)", command):
        reasons.append("touches or reads .env-style paths")
    if "host_to_vps.sh" in command:
        reasons.append("runs VPS deploy script (host_to_vps.sh)")
    if "scripts/release.sh" in command or "./scripts/release.sh" in command:
        reasons.append("runs one-shot release pipeline (release.sh)")
    if re.search(r"git\s+push\b.*--force", command) or re.search(
        r"git\s+push\s+-f\b", command
    ):
        reasons.append("git force push")
    return reasons


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"permission": "allow"}))
        return

    command = str(data.get("command") or "")
    hits = _reasons(command)
    if hits:
        detail = "; ".join(hits)
        print(
            json.dumps(
                {
                    "permission": "ask",
                    "user_message": (
                        "Shell command flagged by project hook "
                        f"({detail}). Review before running."
                    ),
                    "agent_message": f"shell_gate: {detail}",
                }
            )
        )
    else:
        print(json.dumps({"permission": "allow"}))


if __name__ == "__main__":
    main()
