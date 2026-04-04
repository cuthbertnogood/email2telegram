#!/usr/bin/env bash
# Run a command and mirror stdout/stderr to logs/last-run.log for sharing with the AI (@logs/last-run.log).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$ROOT/logs"
LOG="$ROOT/logs/last-run.log"
if [[ $# -eq 0 ]]; then
  echo "Usage: $0 <command> [args...]" >&2
  echo "Example: $0 python src/imap_probe.py" >&2
  exit 1
fi
cd "$ROOT"
"$@" 2>&1 | tee "$LOG"
exit "${PIPESTATUS[0]}"
