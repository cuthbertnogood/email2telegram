#!/usr/bin/env bash
# Build multi-arch image and push to Docker Hub (buildx --push).
#
# Steps (default):
#   1) bump MINOR in VERSION (skip with NO_BUMP=1 or --no-bump)
#   2) docker buildx build linux/amd64 + linux/arm64
#   3) push tags to Docker Hub (requires docker login first)
#
# Usage (from repo root or any cwd — script cds to root):
#   docker login -u YOUR_HUB_USER   # PAT as password
#   ./scripts/host_to_docker_hub.sh
#
# Configure via repo .env (see .env.example): DOCKER_USER, optional TAG, NO_BUMP.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Load .env for DOCKER_USER (and TAG, etc.). Value already in shell wins for DOCKER_USER.
_du_was_set=0
[[ -n "${DOCKER_USER+x}" ]] && _du_was_set=1
_saved_docker_user="${DOCKER_USER-}"
if [[ -f "$ROOT/.env" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT/scripts/dotenv.sh"
  dotenv_load "$ROOT/.env"
fi
if [[ "$_du_was_set" -eq 1 ]]; then
  DOCKER_USER="$_saved_docker_user"
fi

usage() {
  cat <<'EOF'
host_to_docker_hub.sh — Docker Hub: bump MINOR (optional), build, push.

What it does:
  1. By default: increment MINOR in VERSION (in bash).
  2. buildx build for linux/amd64 and linux/arm64.
  3. Push to Docker Hub (same as build; no separate docker push).

Requires: docker login (PAT as password), buildx builder capable of --push.

  docker login -u YOUR_HUB_USER
  ./scripts/host_to_docker_hub.sh

  # Or override .env / org account:
  DOCKER_USER=otherhub ./scripts/host_to_docker_hub.sh

Optional (shell or .env):

  TAG=mytag ./scripts/host_to_docker_hub.sh
  NO_BUMP=1 ./scripts/host_to_docker_hub.sh
  ./scripts/host_to_docker_hub.sh --no-bump

Put DOCKER_USER=... in .env (see .env.example) to avoid exporting it every time.

Tags pushed: YOUR_HUB_USER/email2telegram:TAG and :GIT_SHORT_SHA (or :local).
EOF
}

bump_docker_minor() {
  local raw major minor patch
  raw="$(tr -d '[:space:]' < "$ROOT/VERSION")"
  if [[ ! "$raw" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
    echo "error: VERSION must be MAJOR.MINOR.PATCH, got: ${raw}" >&2
    return 1
  fi
  major="${BASH_REMATCH[1]}"
  minor="${BASH_REMATCH[2]}"
  patch="${BASH_REMATCH[3]}"
  minor=$((minor + 1))
  printf '%s.%s.%s\n' "$major" "$minor" "$patch" > "$ROOT/VERSION"
  echo "MINOR bumped for Docker Hub build → ${major}.${minor}.${patch}"
}

NO_BUMP="${NO_BUMP:-}"
remaining=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help|help)
      usage
      exit 0
      ;;
    --no-bump)
      NO_BUMP=1
      shift
      ;;
    -*)
      echo "error: unknown option: $1 (try --help)" >&2
      exit 1
      ;;
    *)
      remaining+=("$1")
      shift
      ;;
  esac
done
if [[ ${#remaining[@]} -gt 0 ]]; then
  echo "error: unexpected arguments: ${remaining[*]}" >&2
  exit 1
fi

user="${DOCKER_USER:?Set DOCKER_USER (e.g. in .env) to your Docker Hub username}"
tag="${TAG:-latest}"
image="${user}/email2telegram:${tag}"
sha="$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo local)"

if [[ -z "$NO_BUMP" || "$NO_BUMP" == "0" ]]; then
  bump_docker_minor
fi
ver="$(tr -d '[:space:]' < "$ROOT/VERSION")"

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --build-arg "APP_VERSION=${ver}" \
  -t "$image" \
  -t "${user}/email2telegram:${sha}" \
  --push \
  "$ROOT"

echo "Pushed: $image (+ :${sha}) linux/amd64,linux/arm64 | VERSION=${ver} (commit VERSION after push if it changed)"
