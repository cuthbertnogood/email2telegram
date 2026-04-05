#!/usr/bin/env bash
# Commands aligned with DEPLOY.md and the Docker Hub + VPS runbook.
# Usage: ./scripts/docker-hub-vps.sh <command> [args]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

usage() {
  cat <<'EOF'
docker-hub-vps.sh — build/push image, copy compose to VPS, remote pull/up.

Commands:
  hub-checklist     Print Docker Hub UI steps (repo + PAT).
  hub-build-push    Build and push YOUR_USER/email2telegram:TAG (needs: docker login).
                    Env: DOCKER_USER (required), TAG (default latest).
  scp-compose VPS   scp docker-compose.hub.yml (+ systemd unit) to VPS:/opt/email2telegram/
                    Example: ./scripts/docker-hub-vps.sh scp-compose deploy@203.0.113.10
  vps-install-docker
                    Print one-liner to run ON the VPS (Ubuntu) to install Docker Engine + Compose.
  vps-up-remote VPS [path]
                    SSH: cd path (default /opt/email2telegram), compose pull && up -d.
                    Example: ./scripts/docker-hub-vps.sh vps-up-remote deploy@203.0.113.10
  systemd-hints     Print commands to install optional systemd unit on VPS.

Environment:
  DOCKER_USER       Docker Hub username (for hub-build-push).
  TAG               Image tag (default: latest).
  VPS_SSH_OPTS      Extra ssh options, e.g. '-i ~/.ssh/vps_ed25519'.
EOF
}

hub_checklist() {
  cat <<'EOF'
Docker Hub (do in browser):
1. https://hub.docker.com/ or https://app.docker.com/ — sign in.
2. Repositories → Create repository → name: email2telegram (public or private).
3. PAT: https://hub.docker.com/settings/security → New access token.
4. On your PC: docker login -u YOUR_DOCKERHUB_USER  (password = PAT)

Then run from repo root:
  DOCKER_USER=YOUR_DOCKERHUB_USER ./scripts/docker-hub-vps.sh hub-build-push
EOF
}

hub_build_push() {
  local user="${DOCKER_USER:?Set DOCKER_USER to your Docker Hub username}"
  local tag="${TAG:-latest}"
  local image="${user}/email2telegram:${tag}"
  docker build -t "$image" .
  docker push "$image"
  echo "Pushed: $image"
}

scp_compose() {
  local target="${1:?Usage: ... scp-compose user@host}"
  local opts="${VPS_SSH_OPTS:-}"
  echo "On VPS first (if needed): sudo mkdir -p /opt/email2telegram && sudo chown \"\$USER:\$USER\" /opt/email2telegram"
  # shellcheck disable=SC2086
  scp $opts "$ROOT/docker-compose.hub.yml" "$target:/opt/email2telegram/"
  # shellcheck disable=SC2086
  scp $opts "$ROOT/deploy/email2telegram.service" "$target:/opt/email2telegram/"
  echo "Copied docker-compose.hub.yml and email2telegram.service to ${target}:/opt/email2telegram/"
  echo "On VPS: create .env from .env.example + DOCKER_IMAGE=YOUR_USER/email2telegram:latest; chmod 600 .env"
  echo "Private Hub image: docker login on VPS once before pull."
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
  local opts="${VPS_SSH_OPTS:-}"
  # shellcheck disable=SC2086
  ssh $opts "$target" "cd '$rdir' && docker compose -f docker-compose.hub.yml pull && docker compose -f docker-compose.hub.yml up -d && docker compose -f docker-compose.hub.yml ps"
  echo "Done. Logs: ssh $target 'cd $rdir && docker compose -f docker-compose.hub.yml logs -f'"
}

systemd_hints() {
  cat <<'EOF'
On VPS (after files are in /opt/email2telegram):

  sudo cp /opt/email2telegram/email2telegram.service /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable --now email2telegram.service
  sudo systemctl status email2telegram.service
EOF
}

cmd="${1:-}"
case "$cmd" in
  hub-checklist) hub_checklist ;;
  hub-build-push) hub_build_push ;;
  scp-compose) shift; scp_compose "${1:-}" ;;
  vps-install-docker) vps_install_docker ;;
  vps-up-remote) shift; vps_up_remote "${1:-}" "${2:-}" ;;
  systemd-hints) systemd_hints ;;
  -h|--help|help|"") usage ;;
  *) echo "Unknown command: $cmd"; usage; exit 1 ;;
esac
