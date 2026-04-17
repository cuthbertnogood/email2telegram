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
SERVICE_NAME="${EMAIL2TELEGRAM_SERVICE:-email2telegram}"

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

set -a
. ./.env
set +a

_short_digest() {
  local d="$1"
  if [[ -z "$d" || "$d" == "-" || "$d" == "<none>" ]]; then
    printf -- "-"
    return 0
  fi
  d="${d#sha256:}"
  printf -- "%s" "${d:0:12}"
}

tg_send() {
  local text="$1"
  if [[ -z "${TELEGRAM_BOT_TOKEN:-}" || -z "${TELEGRAM_CHAT_ID:-}" ]]; then
    return 0
  fi
  curl -fsS --max-time 10 \
    -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
    --data-urlencode "text=${text}" >/dev/null || true
}

compose_digest() {
  "$DOCKER" compose -f "$COMPOSE_FILE" images --format json "$SERVICE_NAME" 2>/dev/null \
    | sed -n 's/.*"Digest":"\([^"]*\)".*/\1/p' \
    || true
}

run_pull_or_fail() {
  local output=""
  if ! output=$("$DOCKER" compose -f "$COMPOSE_FILE" pull 2>&1); then
    local tail_lines
    tail_lines=$(printf "%s\n" "$output" | tail -n 10)
    echo "$output" >&2
    tg_send "[hub-update] FAIL: pull on $(hostname). Last lines:\n${tail_lines}"
    exit 1
  fi
  printf "%s\n" "$output"
}

run_up_or_fail() {
  local output=""
  if ! output=$("$DOCKER" compose -f "$COMPOSE_FILE" up -d --force-recreate 2>&1); then
    local tail_lines
    tail_lines=$(printf "%s\n" "$output" | tail -n 10)
    echo "$output" >&2
    tg_send "[hub-update] FAIL: up -d --force-recreate on $(hostname). Last lines:\n${tail_lines}"
    exit 1
  fi
  printf "%s\n" "$output"
}

echo "Updating email2telegram ($ROOT, $COMPOSE_FILE)..."
digest_before="$(compose_digest)"
run_pull_or_fail
digest_after="$(compose_digest)"
if [[ "$digest_before" != "$digest_after" ]]; then
  tg_send "hub-update: digest $(_short_digest "$digest_before") -> $(_short_digest "$digest_after"), recreate started on $(hostname)"
fi
run_up_or_fail
"$DOCKER" compose -f "$COMPOSE_FILE" ps
echo "Done."
