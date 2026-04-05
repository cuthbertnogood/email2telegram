#!/usr/bin/env bash
# Скачивает официальный bootstrap Claude Code и подставляет в download_file
# для curl опции --connect-timeout 30 --max-time 600 (явные таймауты вместо «тишины»).
# Использование: ./scripts/install-claude-code-with-curl-timeouts.sh [stable|latest|VERSION]
set -euo pipefail

BOOTSTRAP_URL="https://storage.googleapis.com/claude-code-dist-86c565f3-f756-42ad-8dfa-d59b1c096819/claude-code-releases/bootstrap.sh"
TMP="$(mktemp)"
PATCHED="$(mktemp)"
cleanup() { rm -f "$TMP" "$PATCHED"; }
trap cleanup EXIT

curl -fsSL --connect-timeout 30 --max-time 120 -L -o "$TMP" "$BOOTSTRAP_URL"

# В bootstrap только вызовы curl в download_file используют «curl -fsSL » — добавляем таймауты.
sed 's/curl -fsSL /curl -fsSL --connect-timeout 30 --max-time 600 /g' "$TMP" > "$PATCHED"

bash "$PATCHED" "$@"
