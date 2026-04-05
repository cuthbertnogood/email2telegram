#!/usr/bin/env bash
# Commands aligned with DEPLOY.md and the Docker Hub + VPS runbook.
# Usage: ./scripts/docker-hub-vps.sh [-p PORT] <command> [args]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# ssh uses -p PORT; scp uses -P PORT (scp's -p means "preserve file times").
vps_ssh_opts() {
  local out=""
  if [[ -n "${VPS_SSH_PORT:-}" ]]; then
    out="-p ${VPS_SSH_PORT}"
  fi
  if [[ -n "${VPS_SSH_OPTS:-}" ]]; then
    out="${out:+$out }${VPS_SSH_OPTS}"
  fi
  printf '%s' "$out"
}

vps_scp_opts() {
  local out=""
  if [[ -n "${VPS_SSH_PORT:-}" ]]; then
    out="-P ${VPS_SSH_PORT}"
  fi
  if [[ -n "${VPS_SSH_OPTS:-}" ]]; then
    out="${out:+$out }${VPS_SSH_OPTS}"
  fi
  printf '%s' "$out"
}

usage() {
  cat <<'EOF'
docker-hub-vps.sh — build/push image, copy compose to VPS, remote pull/up.

Options (before the command):
  -h, --help             Show this help.
  -p PORT, --port PORT   Remote port (passed to ssh as -p, to scp as -P). Or env VPS_SSH_PORT.

Commands:
  hub-checklist     Print Docker Hub UI steps (repo + PAT).
  hub-build-push    Same as scripts/docker-hub-publish.sh (bump MINOR, buildx, push).
                    Env: DOCKER_USER (required), TAG (default latest).
  scp-compose VPS   scp docker-compose.hub.yml, deploy/vps-update-hub.sh, systemd units (main + optional Hub timer) to VPS:/opt/email2telegram/
                    Example: ./scripts/docker-hub-vps.sh -p 2222 scp-compose deploy@203.0.113.10
  vps-install-docker
                    Print one-liner to run ON the VPS (Ubuntu) to install Docker Engine + Compose.
  vps-up-remote VPS [path]
                    SSH: cd path (default /opt/email2telegram), compose pull && up -d.
                    Example: ./scripts/docker-hub-vps.sh -p 2222 vps-up-remote deploy@203.0.113.10
  vps-enable-hub-timer VPS [path]
                    SSH + sudo: install and enable email2telegram-hub-update.timer (10-minute Hub pull).
                    Uses files already in path (e.g. after scp-compose). May prompt for sudo password (-t).
  hub-deploy-vps VPS [path]
                    Full Hub deploy from your PC: scp-compose + vps-up-remote + vps-enable-hub-timer.
                    Requires .env on the VPS (DOCKER_IMAGE, secrets). Private image: docker login on VPS first.
  systemd-hints     Print commands to install optional systemd unit on VPS.

Environment:
  DOCKER_USER       Docker Hub username (for hub-build-push).
  TAG               Image tag (default: latest).
  VPS_SSH_PORT      SSH port if not 22 (alternative to -p).
  VPS_SSH_OPTS      Extra ssh options, e.g. '-i ~/.ssh/vps_ed25519'.
EOF
}

# Non-default SSH port: -p / --port before the subcommand, or env VPS_SSH_PORT.
VPS_SSH_PORT="${VPS_SSH_PORT:-}"
remaining=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
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
      echo "error: unknown option: $1 (use -p PORT before the command)" >&2
      usage >&2
      exit 1
      ;;
    *)
      remaining+=("$1")
      shift
      ;;
  esac
done
set -- "${remaining[@]}"

hub_checklist() {
  cat <<'EOF'
Docker Hub (do in browser):
1. https://hub.docker.com/ or https://app.docker.com/ — sign in.
2. Repositories → Create repository → name: email2telegram (public or private).
3. PAT: https://hub.docker.com/settings/security → New access token.
4. On your PC: docker login -u YOUR_DOCKERHUB_USER  (password = PAT)

Main publish (bump MINOR + build + push):

  DOCKER_USER=YOUR_DOCKERHUB_USER ./scripts/docker-hub-publish.sh

Or the same flow via this helper:

  DOCKER_USER=YOUR_DOCKERHUB_USER ./scripts/docker-hub-vps.sh hub-build-push
EOF
}

hub_build_push() {
  exec "$ROOT/scripts/docker-hub-publish.sh"
}

scp_compose() {
  local target="${1:?Usage: ... scp-compose user@host}"
  local opts
  opts="$(vps_scp_opts)"
  echo "On VPS first (if needed): sudo mkdir -p /opt/email2telegram && sudo chown \"\$USER:\$USER\" /opt/email2telegram"
  # shellcheck disable=SC2086
  scp $opts "$ROOT/docker-compose.hub.yml" "$target:/opt/email2telegram/"
  # shellcheck disable=SC2086
  scp $opts "$ROOT/deploy/vps-update-hub.sh" "$target:/opt/email2telegram/"
  # shellcheck disable=SC2086
  scp $opts "$ROOT/deploy/email2telegram.service" "$target:/opt/email2telegram/"
  # shellcheck disable=SC2086
  scp $opts "$ROOT/deploy/email2telegram-hub-update.service" "$target:/opt/email2telegram/"
  # shellcheck disable=SC2086
  scp $opts "$ROOT/deploy/email2telegram-hub-update.timer" "$target:/opt/email2telegram/"
  echo "Copied docker-compose.hub.yml, vps-update-hub.sh, email2telegram*.service, email2telegram-hub-update.timer to ${target}:/opt/email2telegram/"
  echo "On VPS: create .env from .env.example + DOCKER_IMAGE=YOUR_USER/email2telegram:latest; chmod 600 .env"
  echo "Private Hub image: docker login on VPS once before pull."
  echo "Full sync + pull/up + 10m Hub timer (from PC, after .env exists): ./scripts/docker-hub-vps.sh hub-deploy-vps ${target}"
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

vps_up_remote() {
  local target="${1:?Usage: ... vps-up-remote user@host [remote_dir]}"
  local rdir="${2:-/opt/email2telegram}"
  local opts
  opts="$(vps_ssh_opts)"
  # shellcheck disable=SC2086
  ssh $opts "$target" "cd $(printf %q "$rdir") && docker compose -f docker-compose.hub.yml pull && docker compose -f docker-compose.hub.yml up -d && docker compose -f docker-compose.hub.yml ps"
  # shellcheck disable=SC2086
  echo "Done. Logs: ssh $opts $target 'cd $(printf %q "$rdir") && docker compose -f docker-compose.hub.yml logs -f'"
}

# Remote dir as single shell word for ssh (spaces/special chars safe on the PC side).
vps_enable_hub_timer() {
  local target="${1:?Usage: ... vps-enable-hub-timer user@host [remote_dir]}"
  local rdir="${2:-/opt/email2telegram}"
  local opts
  opts="$(vps_ssh_opts)"
  local q
  q="$(printf %q "$rdir")"
  # shellcheck disable=SC2086
  ssh $opts -t "$target" "cd $q && chmod +x vps-update-hub.sh 2>/dev/null || true; sudo cp email2telegram-hub-update.service /etc/systemd/system/ && sudo cp email2telegram-hub-update.timer /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable --now email2telegram-hub-update.timer && sudo systemctl list-timers email2telegram-hub-update.timer --no-pager"
}

hub_deploy_vps() {
  local target="${1:?Usage: ... hub-deploy-vps user@host [remote_dir]}"
  local rdir="${2:-/opt/email2telegram}"
  scp_compose "$target"
  vps_up_remote "$target" "$rdir"
  vps_enable_hub_timer "$target" "$rdir"
  echo "hub-deploy-vps: compose files synced, stack pull/up done, Hub pull timer enabled (see journalctl -u email2telegram-hub-update.service)."
}

systemd_hints() {
  cat <<'EOF'
On VPS (after files are in /opt/email2telegram):

  sudo cp /opt/email2telegram/email2telegram.service /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable --now email2telegram.service
  sudo systemctl status email2telegram.service

Or from your PC (after .env exists on the VPS; sudo may ask for a password):

  ./scripts/docker-hub-vps.sh vps-enable-hub-timer YOUR_USER@VPS_HOST

Manual equivalent (see DEPLOY.md section 7):

  sudo cp /opt/email2telegram/email2telegram-hub-update.service /etc/systemd/system/
  sudo cp /opt/email2telegram/email2telegram-hub-update.timer /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable --now email2telegram-hub-update.timer
  sudo systemctl list-timers email2telegram-hub-update.timer
EOF
}

cmd="${1:-}"
case "$cmd" in
  hub-checklist) hub_checklist ;;
  hub-build-push) hub_build_push ;;
  scp-compose) shift; scp_compose "${1:-}" ;;
  vps-install-docker) vps_install_docker ;;
  vps-up-remote) shift; vps_up_remote "${1:-}" "${2:-}" ;;
  vps-enable-hub-timer) shift; vps_enable_hub_timer "${1:-}" "${2:-}" ;;
  hub-deploy-vps) shift; hub_deploy_vps "${1:-}" "${2:-}" ;;
  systemd-hints) systemd_hints ;;
  -h|--help|help|"") usage ;;
  *) echo "Unknown command: $cmd"; usage; exit 1 ;;
esac
