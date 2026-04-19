#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$ROOT"

scan_history=0
image_ref="${DOCKER_IMAGE:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --history)
      scan_history=1
      shift
      ;;
    --image)
      if [[ $# -lt 2 ]]; then
        echo "FAIL: --image requires value" >&2
        exit 1
      fi
      image_ref="$2"
      shift 2
      ;;
    -h|--help)
      cat <<'EOF'
scan_secrets.sh - repo/image secret leak scanner

Usage:
  .cursor/skills/security-audit/scripts/scan_secrets.sh [--history] [--image IMAGE]

Options:
  --history      Scan git history as well
  --image IMAGE  Inspect this image instead of DOCKER_IMAGE
EOF
      exit 0
      ;;
    *)
      echo "FAIL: unknown option: $1" >&2
      exit 1
      ;;
  esac
done

fails=0
warns=0

ok() { echo "OK: $*"; }
warn() { echo "WARN: $*"; warns=$((warns + 1)); }
fail() { echo "FAIL: $*"; fails=$((fails + 1)); }

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    fail "missing required command: $1"
  fi
}

require_cmd git
require_cmd grep

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  fail "not a git repository: $ROOT"
fi

check_ignore_contains() {
  local file="$1"
  local pat="$2"
  if [[ ! -f "$file" ]]; then
    fail "missing required file: $file"
    return
  fi
  if grep -Eq "^${pat}\r?$" "$file"; then
    ok "${file} contains '${pat}'"
  else
    fail "${file} missing '${pat}'"
  fi
}

check_ignore_contains ".gitignore" "\\.env"
check_ignore_contains ".gitignore" "logs/"
check_ignore_contains ".gitignore" "\\.state\\.json"
check_ignore_contains ".dockerignore" "\\.env"
check_ignore_contains ".dockerignore" "logs"

if git ls-files | grep -Eq '(^|/)\.env$|(^|/)\.env\.local$'; then
  fail ".env-like files are tracked in git"
else
  ok "no tracked .env-like files in git index"
fi

secret_pattern='(IMAP_PASS=|TELEGRAM_BOT_TOKEN=|ghp_[A-Za-z0-9]{30,}|ghu_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,})'

if git grep -nHE "$secret_pattern" -- . ':(exclude).cursor/skills/security-audit/scripts/scan_secrets.sh' 2>/dev/null | grep -Ev '(^|:)\.env\.example:|\.md:|\.plan\.md:' >/tmp/security_scan_workspace_hits.txt; then
  fail "secret-like patterns found in workspace files"
  sed 's/^/  /' /tmp/security_scan_workspace_hits.txt
else
  ok "no secret signatures found in workspace scan"
fi
rm -f /tmp/security_scan_workspace_hits.txt

if [[ "$scan_history" -eq 1 ]]; then
  if git log -p --all -- . ':!.cursor/plans' | grep -nE "$secret_pattern" >/tmp/security_scan_history_hits.txt 2>/dev/null; then
    fail "secret-like patterns found in git history"
    sed 's/^/  /' /tmp/security_scan_history_hits.txt
  else
    ok "no secret signatures found in git history scan"
  fi
  rm -f /tmp/security_scan_history_hits.txt
else
  warn "git history scan skipped (use --history for deep scan)"
fi

if [[ -z "$image_ref" ]]; then
  if [[ -n "${DOCKER_USER:-}" ]]; then
    image_ref="${DOCKER_USER}/email2telegram:${TAG:-latest}"
  fi
fi

if [[ -z "$image_ref" ]]; then
  warn "image inspect skipped (set DOCKER_IMAGE or DOCKER_USER or use --image)"
else
  if ! command -v docker >/dev/null 2>&1; then
    warn "docker command not found, image scan skipped"
  elif ! docker image inspect "$image_ref" >/dev/null 2>&1; then
    warn "image not found locally: $image_ref"
  else
    ok "scanning image: $image_ref"
    cid="$(docker create "$image_ref" 2>/dev/null || true)"
    if [[ -z "$cid" ]]; then
      warn "unable to create temp container for image filesystem scan"
    else
      tmp_tar="$(mktemp -t security-image-XXXXXX.tar)"
      if docker export "$cid" >"$tmp_tar" 2>/dev/null; then
        if tar -tf "$tmp_tar" | grep -nE '(^|/)\.env($|[^/]*$)|(^|/)\.env\.[^/]+$|(^|/)(id_rsa|id_ed25519)(\.pub)?$|(^|/)(.*private.*key.*|.*secret.*)\.(pem|key)$' >/tmp/security_image_hits.txt 2>/dev/null; then
          fail "suspicious secret files present in image filesystem"
          sed 's/^/  /' /tmp/security_image_hits.txt
        else
          ok "no obvious secret files found in image filesystem"
        fi
      else
        warn "docker export failed for image filesystem scan"
      fi
      rm -f "$tmp_tar" /tmp/security_image_hits.txt
      docker rm "$cid" >/dev/null 2>&1 || true
    fi

    if docker inspect "$image_ref" | grep -nE '(IMAP_PASS|TELEGRAM_BOT_TOKEN|PASSWORD=|SECRET=|TOKEN=)' >/tmp/security_image_env_hits.txt 2>/dev/null; then
      fail "image inspect output includes secret-like env keys"
      sed 's/^/  /' /tmp/security_image_env_hits.txt
    else
      ok "no secret-like env keys found in image config"
    fi
    rm -f /tmp/security_image_env_hits.txt
  fi
fi

echo "RESULT: fails=${fails}, warns=${warns}"
if [[ "$fails" -gt 0 ]]; then
  exit 1
fi
