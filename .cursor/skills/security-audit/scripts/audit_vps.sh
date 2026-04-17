#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$ROOT"

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

target="${1:-}"
remote_dir="${2:-${VPS_REMOTE_DIR:-/opt/email2telegram}}"
expected_image="${DOCKER_IMAGE:-}"

if [[ -z "$target" ]]; then
  if [[ -n "${VPS_USER:-}" && -n "${VPS_HOST:-}" ]]; then
    target="${VPS_USER}@${VPS_HOST}"
  else
    echo "FAIL: pass user@host or set VPS_USER and VPS_HOST in .env" >&2
    exit 1
  fi
fi

ssh_opts=()
if [[ -n "${VPS_SSH_PORT:-}" ]]; then
  ssh_opts+=("-p" "${VPS_SSH_PORT}")
fi
if [[ -n "${VPS_SSH_OPTS:-}" ]]; then
  # shellcheck disable=SC2206
  extra_opts=(${VPS_SSH_OPTS})
  ssh_opts+=("${extra_opts[@]}")
fi

fails=0
warns=0
ok() { echo "OK: $*"; }
warn() { echo "WARN: $*"; warns=$((warns + 1)); }
fail() { echo "FAIL: $*"; fails=$((fails + 1)); }

run_remote() {
  local cmd="$1"
  ssh "${ssh_opts[@]}" "$target" "bash -lc $(printf %q "$cmd")"
}

echo "INFO: target=$target remote_dir=$remote_dir"

env_perm="$(run_remote "if [[ -f $(printf %q "$remote_dir")/.env ]]; then stat -c '%a' $(printf %q "$remote_dir")/.env; else echo missing; fi" 2>/dev/null || true)"
if [[ "$env_perm" == "600" ]]; then
  ok ".env permission is 600"
elif [[ "$env_perm" == "missing" || -z "$env_perm" ]]; then
  fail ".env not found on VPS at ${remote_dir}/.env"
else
  fail ".env permission is ${env_perm}, expected 600"
fi

sshd_output="$(run_remote "if [[ -r /etc/ssh/sshd_config ]]; then sudo grep -E '^(PasswordAuthentication|PermitRootLogin)' /etc/ssh/sshd_config || true; else echo no_access; fi" 2>/dev/null || true)"
if [[ "$sshd_output" == *"PasswordAuthentication no"* ]]; then
  ok "PasswordAuthentication is disabled"
else
  warn "could not confirm PasswordAuthentication no"
fi
if [[ "$sshd_output" == *"PermitRootLogin no"* ]]; then
  ok "PermitRootLogin is disabled"
else
  warn "could not confirm PermitRootLogin no"
fi

compose_ps="$(run_remote "cd $(printf %q "$remote_dir") && docker compose -f docker-compose.hub.yml ps --format json 2>/dev/null || docker compose -f docker-compose.hub.yml ps" 2>/dev/null || true)"
if [[ -z "$compose_ps" ]]; then
  fail "docker compose ps returned empty output"
elif [[ "$compose_ps" == *"running"* || "$compose_ps" == *"Up"* ]]; then
  ok "docker compose reports running container"
else
  warn "container may be stopped; inspect docker compose ps output manually"
  echo "$compose_ps"
fi

port_lines="$(run_remote "ss -tlnp | grep -nE ':(22|80|443|8080|8443)\\s' || true" 2>/dev/null || true)"
if [[ -z "$port_lines" ]]; then
  ok "no common public service ports (except SSH) detected"
else
  warn "open common ports detected; verify exposure policy"
  echo "$port_lines"
fi

if [[ -n "$expected_image" ]]; then
  running_image="$(run_remote "cd $(printf %q "$remote_dir") && docker compose -f docker-compose.hub.yml ps -q email2telegram | xargs -r docker inspect --format '{{.Config.Image}}'" 2>/dev/null || true)"
  if [[ -z "$running_image" ]]; then
    warn "unable to determine running image name"
  elif [[ "$running_image" == "$expected_image" ]]; then
    ok "running image matches expected DOCKER_IMAGE"
  else
    fail "running image '${running_image}' does not match expected '${expected_image}'"
  fi
else
  warn "DOCKER_IMAGE not set locally; image-match check skipped"
fi

echo "RESULT: fails=${fails}, warns=${warns}"
if [[ "$fails" -gt 0 ]]; then
  exit 1
fi
