#!/usr/bin/env bash
# Back-compat alias for scripts/docker-hub-build-push.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$ROOT/scripts/docker-hub-build-push.sh" "$@"
