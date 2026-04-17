#!/usr/bin/env bash
# One-command local git add/commit/push to GitHub.
# Usage:
#   ./scripts/host_to_github.sh
#   ./scripts/host_to_github.sh -m "feat: update parser"
#   AUTO_BUMP=1 ./scripts/host_to_github.sh -m "chore: sync"
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

usage() {
  cat <<'EOF'
host_to_github.sh — stage all, commit (if needed), and push current branch.

Usage:
  ./scripts/host_to_github.sh
  ./scripts/host_to_github.sh -m "your commit message"
  AUTO_BUMP=1 ./scripts/host_to_github.sh -m "chore: update"

Behavior:
  1) git add -A
  2) create commit if staged changes exist
  3) push current branch (with -u origin <branch> if no upstream)

Options:
  -m, --message TEXT   Commit message (default: chore: update <branch> <UTC timestamp>)
  -h, --help           Show help

Env:
  AUTO_BUMP=1          Run python3 scripts/bump_code_patch.py before git add -A
EOF
}

commit_message=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help|help)
      usage
      exit 0
      ;;
    -m|--message)
      if [[ $# -lt 2 ]]; then
        echo "error: $1 requires a value" >&2
        exit 1
      fi
      commit_message="$2"
      shift 2
      ;;
    -*)
      echo "error: unknown option: $1 (try --help)" >&2
      exit 1
      ;;
    *)
      echo "error: unexpected argument: $1 (try --help)" >&2
      exit 1
      ;;
  esac
done

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
  echo "error: not a git repository: $ROOT" >&2
  exit 1
}

remote_url="$(git remote get-url origin 2>/dev/null || true)"
if [[ -z "$remote_url" ]]; then
  echo "error: remote 'origin' is not configured" >&2
  exit 1
fi

if [[ "${AUTO_BUMP:-}" == "1" ]]; then
  python3 "$ROOT/scripts/bump_code_patch.py"
fi

branch="$(git symbolic-ref --short HEAD 2>/dev/null || true)"
if [[ -z "$branch" ]]; then
  echo "error: detached HEAD; checkout a branch first" >&2
  exit 1
fi

git add -A

if git diff --cached --quiet; then
  echo "No staged changes after git add -A."
else
  if [[ -z "$commit_message" ]]; then
    ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    commit_message="chore: update ${branch} ${ts}"
  fi
  git commit -m "$commit_message"
fi

upstream="$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"
if [[ -n "$upstream" ]]; then
  git push
else
  git push -u origin "$branch"
fi

echo "Done: branch '${branch}' pushed to origin."
