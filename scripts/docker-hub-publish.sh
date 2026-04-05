#!/usr/bin/env bash
# Single entry point: bump MINOR → multi-arch buildx → push to Docker Hub.
# Always runs scripts/bump_docker_minor.py before the image is built.
#
# Usage (from anywhere, after docker login):
#   DOCKER_USER=yourhubuser ./scripts/docker-hub-publish.sh
#
# Env:
#   DOCKER_USER  (required) Docker Hub username / org
#   TAG          (optional)  image tag, default: latest
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

usage() {
  cat <<'EOF'
docker-hub-publish.sh — bump MINOR, build multi-arch image, push to Docker Hub.

Requires: docker login (PAT as password), docker buildx with a builder that can push.

  DOCKER_USER=YOUR_HUB_USER ./scripts/docker-hub-publish.sh

Optional:

  TAG=mytag DOCKER_USER=YOUR_HUB_USER ./scripts/docker-hub-publish.sh

Tags pushed: YOUR_HUB_USER/email2telegram:TAG and :GIT_SHORT_SHA (or :local if not a git repo).
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || "${1:-}" == "help" ]]; then
  usage
  exit 0
fi

user="${DOCKER_USER:?Set DOCKER_USER to your Docker Hub username}"
tag="${TAG:-latest}"
image="${user}/email2telegram:${tag}"
sha="$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo local)"

python3 "$ROOT/scripts/bump_docker_minor.py"
ver="$(tr -d '[:space:]' < "$ROOT/VERSION")"

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --build-arg "APP_VERSION=${ver}" \
  -t "$image" \
  -t "${user}/email2telegram:${sha}" \
  --push \
  "$ROOT"

echo "Pushed: $image (+ :${sha}) linux/amd64,linux/arm64 | VERSION=${ver} (commit this file after push)"
