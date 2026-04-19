#!/usr/bin/env bash
# From your PC: sync deploy files to VPS, remote docker compose pull/up, Hub timer, hints.
# Loads repo .env for VPS_USER, VPS_HOST, VPS_SSH_PORT, VPS_REMOTE_DIR (see docs/host-to-vps.md).
#
# Usage (from repo root or any cwd — script cds to root):
#   ./scripts/host_to_vps.sh sync              # scp deploy files (uses .env)
#   ./scripts/host_to_vps.sh pull-up           # docker compose pull && up on VPS
#   ./scripts/host_to_vps.sh enable-timer      # systemd Hub pull timer
#   ./scripts/host_to_vps.sh deploy            # sync + pull-up + enable-timer
#   ./scripts/host_to_vps.sh sync user@host [/other/dir]   # override .env for this run
#
# Options before the command: -p PORT  (or VPS_SSH_PORT in .env)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

_w_vps_user=0
[[ -n "${VPS_USER+x}" ]] && _w_vps_user=1
_s_vps_user="${VPS_USER-}"
_w_vps_host=0
[[ -n "${VPS_HOST+x}" ]] && _w_vps_host=1
_s_vps_host="${VPS_HOST-}"
_w_vps_port=0
[[ -n "${VPS_SSH_PORT+x}" ]] && _w_vps_port=1
_s_vps_port="${VPS_SSH_PORT-}"
_w_vps_rdir=0
[[ -n "${VPS_REMOTE_DIR+x}" ]] && _w_vps_rdir=1
_s_vps_rdir="${VPS_REMOTE_DIR-}"
_w_vps_ssh_opts=0
[[ -n "${VPS_SSH_OPTS+x}" ]] && _w_vps_ssh_opts=1
_s_vps_ssh_opts="${VPS_SSH_OPTS-}"

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

if [[ "$_w_vps_user" -eq 1 ]]; then VPS_USER="$_s_vps_user"; fi
if [[ "$_w_vps_host" -eq 1 ]]; then VPS_HOST="$_s_vps_host"; fi
if [[ "$_w_vps_port" -eq 1 ]]; then VPS_SSH_PORT="$_s_vps_port"; fi
if [[ "$_w_vps_rdir" -eq 1 ]]; then VPS_REMOTE_DIR="$_s_vps_rdir"; fi
if [[ "$_w_vps_ssh_opts" -eq 1 ]]; then VPS_SSH_OPTS="$_s_vps_ssh_opts"; fi

vps_ssh_opts() {
  # Keep long `docker compose pull` sessions alive through NAT/firewalls; later -o flags win if duplicated in VPS_SSH_OPTS.
  local out="-o ServerAliveInterval=15 -o ServerAliveCountMax=8 -o TCPKeepAlive=yes"
  if [[ -n "${VPS_SSH_PORT:-}" ]]; then
    out="${out} -p ${VPS_SSH_PORT}"
  fi
  if [[ -n "${VPS_SSH_OPTS:-}" ]]; then
    out="${out} ${VPS_SSH_OPTS}"
  fi
  if [[ -n "${VPS_SSH_VERBOSE:-}" ]]; then
    out="${out} -v"
  fi
  printf '%s' "$out"
}

# Non-interactive ssh uses a minimal PATH; login shell picks up /etc/profile and ~/.profile (where docker often appears).
remote_sh() {
  local target="$1"
  local inner="$2"
  local want_tty="${3:-}"
  local opts
  opts="$(vps_ssh_opts)"
  if [[ "$want_tty" == "1" ]]; then
    # shellcheck disable=SC2086
    ssh $opts -t "$target" "bash -lc $(printf %q "$inner")"
  else
    # shellcheck disable=SC2086
    ssh $opts "$target" "bash -lc $(printf %q "$inner")"
  fi
}

vps_scp_opts() {
  local out="-o ServerAliveInterval=15 -o ServerAliveCountMax=8 -o TCPKeepAlive=yes"
  if [[ -n "${VPS_SSH_PORT:-}" ]]; then
    out="${out} -P ${VPS_SSH_PORT}"
  fi
  if [[ -n "${VPS_SSH_OPTS:-}" ]]; then
    out="${out} ${VPS_SSH_OPTS}"
  fi
  printf '%s' "$out"
}

resolve_target() {
  local o="${1:-}"
  if [[ -n "$o" ]]; then
    printf '%s' "$o"
    return 0
  fi
  if [[ -n "${VPS_USER:-}" && -n "${VPS_HOST:-}" ]]; then
    printf '%s' "${VPS_USER}@${VPS_HOST}"
    return 0
  fi
  echo "error: set VPS_USER and VPS_HOST in .env or pass user@host" >&2
  exit 1
}

resolve_rdir() {
  local o="${1:-}"
  if [[ -n "$o" ]]; then
    printf '%s' "${o%/}"
    return 0
  fi
  printf '%s' "${VPS_REMOTE_DIR:-/opt/email2telegram}"
}

usage() {
  cat <<'EOF'
host_to_vps.sh — sync deploy files to VPS, remote compose pull/up, Hub timer (from your PC).

Defaults from .env: VPS_USER, VPS_HOST, optional VPS_SSH_PORT, VPS_REMOTE_DIR, VPS_SSH_OPTS, VPS_SSH_VERBOSE, VPS_PULL_UP_RETRIES (default 3, backoff between SSH attempts for pull-up).
Remote docker runs via bash -lc (login PATH). Debug: VPS_SSH_VERBOSE=1.

  ./scripts/host_to_vps.sh [-p PORT] sync   [user@host [REMOTE_DIR]]
  ./scripts/host_to_vps.sh [-p PORT] pull-up   [user@host [REMOTE_DIR]]
  ./scripts/host_to_vps.sh [-p PORT] enable-timer   [user@host [REMOTE_DIR]]
  ./scripts/host_to_vps.sh [-p PORT] deploy   [user@host [REMOTE_DIR]]   # sync + pull-up + enable-timer

  ./scripts/host_to_vps.sh hub-checklist      # Docker Hub browser + PAT reminder
  ./scripts/host_to_vps.sh install-docker     # print Ubuntu Docker install one-liner
  ./scripts/host_to_vps.sh systemd-hints      # optional systemd unit for the stack

Docker Hub image build/push: ./scripts/host_to_docker_hub.sh

Full guide: docs/host-to-vps.md

Debug SSH: VPS_SSH_VERBOSE=1 ./scripts/host_to_vps.sh pull-up
EOF
}

VPS_SSH_PORT="${VPS_SSH_PORT:-}"
remaining=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help|help)
      usage
      exit 0
      ;;
    -p|--port)
      if [[ $# -lt 2 ]]; then
        echo "error: $1 requires a port number" >&2
        exit 1
      fi
      VPS_SSH_PORT="$2"
      shift 2
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

cmd="${remaining[0]:-}"
if [[ -z "$cmd" ]]; then
  usage >&2
  exit 1
fi
set -- "${remaining[@]:1}"

hub_checklist() {
  cat <<'EOF'
Docker Hub (do in browser):
1. https://hub.docker.com/ or https://app.docker.com/ — sign in.
2. Repositories → Create repository → name: email2telegram (public or private).
3. PAT: https://hub.docker.com/settings/security → New access token.
4. On your PC: docker login -u YOUR_DOCKERHUB_USER  (password = PAT)

Build and push (bump MINOR by default):

  ./scripts/host_to_docker_hub.sh

Put DOCKER_USER in repo .env (see .env.example), or export it.

Details: docs/host-to-docker-hub.md
VPS sync / deploy from PC: docs/host-to-vps.md
EOF
}

cmd_sync() {
  local target rdir dest opts
  target="$(resolve_target "${1:-}")"
  rdir="$(resolve_rdir "${2:-}")"
  dest="${target}:${rdir}/"
  opts="$(vps_scp_opts)"

  echo "Tip on VPS (if needed): sudo mkdir -p $(printf %q "$rdir") && sudo chown \"\$USER:\$USER\" $(printf %q "$rdir")"

  local f
  for f in \
    "$ROOT/docker-compose.hub.yml" \
    "$ROOT/deploy/vps-update-hub.sh" \
    "$ROOT/deploy/email2telegram.service" \
    "$ROOT/deploy/email2telegram-hub-update.service" \
    "$ROOT/deploy/email2telegram-hub-update.timer"
  do
    [[ -f "$f" ]] || { echo "error: missing file $f" >&2; exit 1; }
  done

  # shellcheck disable=SC2086
  scp $opts "$ROOT/docker-compose.hub.yml" "$dest"
  # shellcheck disable=SC2086
  scp $opts "$ROOT/deploy/vps-update-hub.sh" "$dest"
  # shellcheck disable=SC2086
  scp $opts "$ROOT/deploy/email2telegram.service" "$dest"
  # shellcheck disable=SC2086
  scp $opts "$ROOT/deploy/email2telegram-hub-update.service" "$dest"
  # shellcheck disable=SC2086
  scp $opts "$ROOT/deploy/email2telegram-hub-update.timer" "$dest"

  echo "Synced to ${target}:${rdir}/"
  echo "On VPS: .env with DOCKER_IMAGE + secrets; chmod 600 .env; chmod +x ${rdir}/vps-update-hub.sh"
  echo "Then: ./scripts/host_to_vps.sh pull-up   (same .env targets this host)"
}

cmd_pull_up() {
  local target rdir opts inner log_inner attempt max delay
  target="$(resolve_target "${1:-}")"
  rdir="$(resolve_rdir "${2:-}")"
  inner="cd $(printf %q "$rdir") && set -euo pipefail && docker compose -f docker-compose.hub.yml pull && docker compose -f docker-compose.hub.yml up -d --force-recreate && docker compose -f docker-compose.hub.yml ps"
  max="${VPS_PULL_UP_RETRIES:-3}"
  [[ "$max" =~ ^[1-9][0-9]*$ ]] || max=3
  attempt=1
  delay=5
  while [[ "$attempt" -le "$max" ]]; do
    if remote_sh "$target" "$inner" ""; then
      break
    fi
    if [[ "$attempt" -ge "$max" ]]; then
      echo "error: pull-up failed after ${max} attempt(s) (SSH or remote docker compose)" >&2
      exit 1
    fi
    echo "pull-up: attempt ${attempt} failed, retrying in ${delay}s..." >&2
    sleep "$delay"
    delay=$((delay + 5))
    attempt=$((attempt + 1))
  done
  opts="$(vps_ssh_opts)"
  log_inner="cd $(printf %q "$rdir") && docker compose -f docker-compose.hub.yml logs -f"
  # shellcheck disable=SC2086
  echo "Done. Logs: ssh $opts $target bash -lc $(printf %q "$log_inner")"
}

cmd_enable_timer() {
  local target rdir inner
  target="$(resolve_target "${1:-}")"
  rdir="$(resolve_rdir "${2:-}")"
  inner="cd $(printf %q "$rdir") && chmod +x vps-update-hub.sh 2>/dev/null || true; sudo cp email2telegram-hub-update.service /etc/systemd/system/ && sudo cp email2telegram-hub-update.timer /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable --now email2telegram-hub-update.timer && sudo systemctl list-timers email2telegram-hub-update.timer --no-pager"
  remote_sh "$target" "$inner" "1"
}

cmd_deploy() {
  local target rdir
  target="$(resolve_target "${1:-}")"
  rdir="$(resolve_rdir "${2:-}")"
  cmd_sync "$target" "$rdir"
  cmd_pull_up "$target" "$rdir"
  cmd_enable_timer "$target" "$rdir"
  echo "deploy: files synced, stack updated, Hub pull timer enabled (see journalctl -u email2telegram-hub-update.service)."
}

vps_install_docker() {
  cat <<'EOF'
Run ON the VPS (Ubuntu 22.04/24.04), with sudo:

  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER"
  # log out and back in, then:
  docker --version && docker compose version

Official docs (if you prefer apt repo over convenience script):
  https://docs.docker.com/engine/install/ubuntu/
  https://docs.docker.com/compose/install/linux/
EOF
}

systemd_hints() {
  cat <<EOF
On VPS (after files are in ${VPS_REMOTE_DIR:-/opt/email2telegram}):

  sudo cp ${VPS_REMOTE_DIR:-/opt/email2telegram}/email2telegram.service /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable --now email2telegram.service
  sudo systemctl status email2telegram.service

Or from your PC (after .env on the VPS; sudo may prompt):

  ./scripts/host_to_vps.sh enable-timer

Manual equivalent (see DEPLOY.md section 7):

  sudo cp ${VPS_REMOTE_DIR:-/opt/email2telegram}/email2telegram-hub-update.service /etc/systemd/system/
  sudo cp ${VPS_REMOTE_DIR:-/opt/email2telegram}/email2telegram-hub-update.timer /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable --now email2telegram-hub-update.timer
  sudo systemctl list-timers email2telegram-hub-update.timer
EOF
}

case "$cmd" in
  sync) cmd_sync "${1:-}" "${2:-}" ;;
  pull-up) cmd_pull_up "${1:-}" "${2:-}" ;;
  enable-timer) cmd_enable_timer "${1:-}" "${2:-}" ;;
  deploy) cmd_deploy "${1:-}" "${2:-}" ;;
  hub-checklist) hub_checklist ;;
  install-docker) vps_install_docker ;;
  systemd-hints) systemd_hints ;;
  *)
    echo "error: unknown command: $cmd" >&2
    usage >&2
    exit 1
    ;;
esac
