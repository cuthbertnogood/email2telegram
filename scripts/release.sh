#!/usr/bin/env bash
# One-shot release from PC:
#   (auto-commit if git dirty) -> test -> Docker Hub build/push -> VPS sync -> VPS pull/up
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

usage() {
  cat <<'EOF'
release.sh - one command release: tests, Docker Hub push, VPS deploy, GitHub push.

Usage:
  ./scripts/release.sh [options] [user@host [REMOTE_DIR]]

If the git working tree is dirty, all changes are staged (git add -A) and committed
before the pipeline runs, unless --allow-dirty is set.

Options:
  --no-bump         Do not bump VERSION in host_to_docker_hub.sh (sets NO_BUMP=1)
  --skip-security   Skip security scan script before release checks
  --skip-tests      Skip python3 -m pytest -q
  --allow-dirty     Allow dirty git working tree (skip auto-commit)
  --skip-env-sync   Skip pushing filtered local .env to VPS (secrets/tokens rotation)
  --enable-timer    Also run host_to_vps.sh enable-timer after pull-up
  --no-push-github  Skip host_to_github.sh at the end (default is push)
  --tag TAG         Override TAG for host_to_docker_hub.sh
  -h, --help        Show this help

Examples:
  ./scripts/release.sh
  ./scripts/release.sh --no-bump
  ./scripts/release.sh --skip-tests --enable-timer
  ./scripts/release.sh deploy@203.0.113.10 /opt/email2telegram

Secret rotation (e.g. TELEGRAM_BOT_TOKEN revoked via BotFather):
  1. Edit the new token in local .env.
  2. Run ./scripts/release.sh — filtered .env (no PC-only keys) is pushed to VPS
     and the container is recreated with the new token automatically.

Env (from .env):
  VPS_POST_SYNC_SLEEP  seconds between VPS sync and pull-up if SSH rate-limits connections.
  VPS_SYNC_ENV=0       disable automatic .env sync to VPS (equivalent to --skip-env-sync).
EOF
}

for req in "./scripts/host_to_docker_hub.sh" "./scripts/host_to_vps.sh" "./scripts/host_to_github.sh"; do
  [[ -x "$req" ]] || {
    echo "error: required script missing or not executable: $req" >&2
    exit 1
  }
done

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

NO_BUMP="${NO_BUMP:-}"
TAG="${TAG:-latest}"
SKIP_TESTS=0
SKIP_SECURITY=0
ALLOW_DIRTY=0
ENABLE_TIMER=0
PUSH_GITHUB=1
SYNC_ENV=1
if [[ "${VPS_SYNC_ENV:-1}" == "0" ]]; then
  SYNC_ENV=0
fi
POSITIONAL=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --no-bump)
      NO_BUMP=1
      shift
      ;;
    --skip-tests)
      SKIP_TESTS=1
      shift
      ;;
    --skip-security)
      SKIP_SECURITY=1
      shift
      ;;
    --allow-dirty)
      ALLOW_DIRTY=1
      shift
      ;;
    --skip-env-sync)
      SYNC_ENV=0
      shift
      ;;
    --enable-timer)
      ENABLE_TIMER=1
      shift
      ;;
    --no-push-github)
      PUSH_GITHUB=0
      shift
      ;;
    --tag)
      if [[ $# -lt 2 ]]; then
        echo "error: --tag requires a value" >&2
        exit 1
      fi
      TAG="$2"
      shift 2
      ;;
    -*)
      echo "error: unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done

TARGET="${POSITIONAL[0]:-}"
REMOTE_DIR="${POSITIONAL[1]:-}"
if [[ ${#POSITIONAL[@]} -gt 2 ]]; then
  echo "error: expected at most two positional args: [user@host] [REMOTE_DIR]" >&2
  exit 1
fi

for cmd in docker ssh scp python3 git; do
  command -v "$cmd" >/dev/null 2>&1 || {
    echo "error: required command not found: $cmd" >&2
    exit 1
  }
done

if [[ -z "${DOCKER_USER:-}" ]]; then
  echo "error: DOCKER_USER is required (set in .env or environment)" >&2
  exit 1
fi
if [[ -z "$TARGET" && ( -z "${VPS_USER:-}" || -z "${VPS_HOST:-}" ) ]]; then
  echo "error: VPS_USER and VPS_HOST are required unless user@host is provided" >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  if [[ "$ALLOW_DIRTY" -eq 1 ]]; then
    :
  else
    echo "Git working tree is dirty; staging all changes and committing..."
    git add -A
    if git diff --cached --quiet; then
      echo "error: git reports a dirty tree but nothing was staged (check .gitignore and skip-worktree)" >&2
      exit 1
    fi
    ver_prep="$(tr -d '[:space:]' < "$ROOT/VERSION" 2>/dev/null || echo '?')"
    git commit -m "chore(release): pending changes before release (${ver_prep})"
  fi
fi

sha="$(git rev-parse --short HEAD 2>/dev/null || echo local)"
echo "Release start | sha=${sha} | tag=${TAG} | no_bump=${NO_BUMP:-0} | push_github=${PUSH_GITHUB} | sync_env=${SYNC_ENV}"

if [[ "$SKIP_SECURITY" -ne 1 ]]; then
  echo "[0/9] Running security scan..."
  ./.cursor/skills/security-audit/scripts/scan_secrets.sh
else
  echo "[0/9] Skipping security scan (--skip-security)"
fi

echo "[1/9] README sync check..."
python3 scripts/sync_readme_ru.py --check

if [[ "$SKIP_TESTS" -ne 1 ]]; then
  echo "[2/9] Running tests..."
  python3 -m pytest -q
else
  echo "[2/9] Skipping tests (--skip-tests)"
fi

echo "[3/9] Building and pushing Docker image..."
NO_BUMP="$NO_BUMP" TAG="$TAG" DOCKER_USER="$DOCKER_USER" ./scripts/host_to_docker_hub.sh

echo "[4/9] Verifying image in registry..."
docker buildx imagetools inspect "${DOCKER_USER}/email2telegram:${TAG}" >/dev/null

echo "[5/9] Syncing deploy files to VPS..."
if [[ -n "$TARGET" ]]; then
  ./scripts/host_to_vps.sh sync "$TARGET" "$REMOTE_DIR"
else
  ./scripts/host_to_vps.sh sync
fi

if [[ "$SYNC_ENV" -eq 1 ]]; then
  echo "[6/9] Syncing filtered .env (secrets/tokens) to VPS..."
  if [[ -n "$TARGET" ]]; then
    TAG="$TAG" DOCKER_USER="$DOCKER_USER" ./scripts/host_to_vps.sh sync-env "$TARGET" "$REMOTE_DIR"
  else
    TAG="$TAG" DOCKER_USER="$DOCKER_USER" ./scripts/host_to_vps.sh sync-env
  fi
else
  echo "[6/9] Skipping .env sync (--skip-env-sync or VPS_SYNC_ENV=0)"
fi

if [[ -n "${VPS_POST_SYNC_SLEEP:-}" && "${VPS_POST_SYNC_SLEEP}" =~ ^[1-9][0-9]*$ ]]; then
  echo "[6b/9] VPS_POST_SYNC_SLEEP=${VPS_POST_SYNC_SLEEP}s before pull-up..."
  sleep "$VPS_POST_SYNC_SLEEP"
fi

echo "[7/9] Pulling and recreating container on VPS..."
if [[ -n "$TARGET" ]]; then
  ./scripts/host_to_vps.sh pull-up "$TARGET" "$REMOTE_DIR"
else
  ./scripts/host_to_vps.sh pull-up
fi

if [[ "$ENABLE_TIMER" -eq 1 ]]; then
  echo "[8/9] Enabling systemd timer on VPS..."
  if [[ -n "$TARGET" ]]; then
    ./scripts/host_to_vps.sh enable-timer "$TARGET" "$REMOTE_DIR"
  else
    ./scripts/host_to_vps.sh enable-timer
  fi
else
  echo "[8/9] Skipping timer enable (use --enable-timer)"
fi

if [[ "$PUSH_GITHUB" -eq 1 ]]; then
  echo "[9/9] Pushing project to GitHub..."
  ./scripts/host_to_github.sh
else
  echo "[9/9] Skipping GitHub push (--no-push-github)"
fi

ver="$(tr -d '[:space:]' < "$ROOT/VERSION")"
echo "Release completed | version=${ver} | image=${DOCKER_USER}/email2telegram:${TAG} | sha=${sha} | github_push=${PUSH_GITHUB}"
echo "If VPS deploy failed after push, timer fallback should refresh within ~10 minutes."
