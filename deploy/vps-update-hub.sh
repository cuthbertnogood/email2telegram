#!/usr/bin/env bash
# Run on the VPS: pull the image from Docker Hub and recreate the stack.
# Uses `up -d --force-recreate` so the container is rebuilt from the pulled image
# (not only restarted with a stale local layer).
# Expects docker-compose.hub.yml and .env in the working directory.
#
# Default directory: /opt/email2telegram (override with EMAIL2TELEGRAM_DIR).
# Default compose file: docker-compose.hub.yml (override with EMAIL2TELEGRAM_COMPOSE).
# Docker binary: default /usr/bin/docker for predictable PATH under systemd (override with DOCKER).
#
# Usage:
#   ./vps-update-hub.sh
#   EMAIL2TELEGRAM_DIR=/srv/bot ./vps-update-hub.sh
set -euo pipefail

ROOT="${EMAIL2TELEGRAM_DIR:-/opt/email2telegram}"
COMPOSE_FILE="${EMAIL2TELEGRAM_COMPOSE:-docker-compose.hub.yml}"
DOCKER="${DOCKER:-/usr/bin/docker}"

usage() {
  cat <<'EOF'
vps-update-hub.sh — docker compose pull + up -d --force-recreate for the Hub-based stack.

Environment:
  EMAIL2TELEGRAM_DIR     Project directory (default: /opt/email2telegram)
  EMAIL2TELEGRAM_COMPOSE Compose file name (default: docker-compose.hub.yml)
  DOCKER                 docker CLI path (default: /usr/bin/docker)

Private images: run `docker login` once on this host before pulling.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

cd "$ROOT"

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "error: compose file not found: $ROOT/$COMPOSE_FILE" >&2
  exit 1
fi
if [[ ! -f .env ]]; then
  echo "error: .env not found in $ROOT (create from .env.example, chmod 600)" >&2
  exit 1
fi

echo "Updating email2telegram ($ROOT, $COMPOSE_FILE)..."
"$DOCKER" compose -f "$COMPOSE_FILE" pull
"$DOCKER" compose -f "$COMPOSE_FILE" up -d --force-recreate
"$DOCKER" compose -f "$COMPOSE_FILE" ps
echo "Done."
