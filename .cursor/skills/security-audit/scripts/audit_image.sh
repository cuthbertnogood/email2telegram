#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$ROOT"

image_ref="${1:-}"
if [[ -z "$image_ref" && -n "${DOCKER_IMAGE:-}" ]]; then
  image_ref="$DOCKER_IMAGE"
fi
if [[ -z "$image_ref" && -n "${DOCKER_USER:-}" ]]; then
  image_ref="${DOCKER_USER}/email2telegram:${TAG:-latest}"
fi

if [[ -z "$image_ref" ]]; then
  echo "FAIL: image reference is required (arg1 or DOCKER_IMAGE or DOCKER_USER)" >&2
  exit 1
fi

fails=0
warns=0
ok() { echo "OK: $*"; }
warn() { echo "WARN: $*"; warns=$((warns + 1)); }
fail() { echo "FAIL: $*"; fails=$((fails + 1)); }

if ! command -v docker >/dev/null 2>&1; then
  fail "docker command not found"
  echo "RESULT: fails=${fails}, warns=${warns}"
  exit 1
fi

if ! docker image inspect "$image_ref" >/dev/null 2>&1; then
  fail "image not found locally: $image_ref"
  echo "RESULT: fails=${fails}, warns=${warns}"
  exit 1
fi

user_cfg="$(docker image inspect "$image_ref" --format '{{.Config.User}}')"
if [[ -z "$user_cfg" || "$user_cfg" == "root" || "$user_cfg" == "0" ]]; then
  fail "image runs as root or has empty Config.User"
else
  ok "Config.User is non-root: ${user_cfg}"
fi

health_cfg="$(docker image inspect "$image_ref" --format '{{json .Config.Healthcheck}}')"
if [[ "$health_cfg" == "null" ]]; then
  fail "image has no HEALTHCHECK"
else
  ok "HEALTHCHECK configured"
fi

if docker image inspect "$image_ref" --format '{{range .Config.Env}}{{println .}}{{end}}' | grep -nE '(PASS|PASSWORD|TOKEN|SECRET|KEY)=' >/tmp/security_audit_image_env_hits.txt 2>/dev/null; then
  fail "secret-like env keys found in image Config.Env"
  sed 's/^/  /' /tmp/security_audit_image_env_hits.txt
else
  ok "no secret-like env keys in Config.Env"
fi
rm -f /tmp/security_audit_image_env_hits.txt

size_bytes="$(docker image inspect "$image_ref" --format '{{.Size}}')"
if [[ "$size_bytes" =~ ^[0-9]+$ ]]; then
  size_mb=$((size_bytes / 1024 / 1024))
  if [[ "$size_mb" -gt 200 ]]; then
    warn "image size is large (${size_mb}MB > 200MB)"
  else
    ok "image size looks reasonable (${size_mb}MB)"
  fi
else
  warn "unable to parse image size"
fi

if command -v trivy >/dev/null 2>&1; then
  echo "INFO: running trivy image scan (HIGH,CRITICAL)"
  if trivy image --quiet --severity HIGH,CRITICAL --exit-code 1 "$image_ref"; then
    ok "trivy found no HIGH/CRITICAL vulnerabilities"
  else
    fail "trivy reported HIGH/CRITICAL vulnerabilities"
  fi
else
  warn "trivy not installed; install for CVE scan"
fi

if docker sbom --help >/dev/null 2>&1; then
  ok "docker sbom is available"
elif command -v syft >/dev/null 2>&1; then
  ok "syft is available for SBOM generation"
else
  warn "no SBOM tool found (docker sbom or syft)"
fi

echo "RESULT: fails=${fails}, warns=${warns}"
if [[ "$fails" -gt 0 ]]; then
  exit 1
fi
