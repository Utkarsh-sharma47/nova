#!/usr/bin/env bash
# Phase 1 heuristic secret-pattern scan over tracked / present source files.
# Complements Gitleaks in CI. Exits non-zero on matches. Never uses || true.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Paths that may legitimately discuss secret *patterns* without holding secrets.
EXCLUDE_PATHS=(
  "./.git"
  "./.venv"
  "./venv"
  "./node_modules"
  "./.env.example"
  "./scripts/check-secret-patterns.sh"
  "./SECURITY.md"
  "./docs/deployment/ci-cd.md"
)

is_excluded() {
  local file="$1"
  local rel="${file#./}"
  for ex in "${EXCLUDE_PATHS[@]}"; do
    local ex_rel="${ex#./}"
    if [[ "$rel" == "$ex_rel" || "$rel" == "$ex_rel"/* ]]; then
      return 0
    fi
  done
  return 1
}

# Common accidental-leak patterns (heuristic; Gitleaks is the primary detector).
PATTERNS=(
  'AKIA[0-9A-Z]{16}'
  '-----BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY-----'
  'ghp_[A-Za-z0-9]{36}'
  'github_pat_[A-Za-z0-9_]{20,}'
  'xox[baprs]-[A-Za-z0-9-]{10,}'
  'sk-[A-Za-z0-9]{20,}'
)

FINDINGS=0

echo "==> Scanning for common secret patterns"

while IFS= read -r -d '' file; do
  if is_excluded "$file"; then
    continue
  fi
  # Skip binary-ish files
  if ! grep -Iq . "$file" 2>/dev/null; then
    continue
  fi
  for pattern in "${PATTERNS[@]}"; do
    if matches="$(grep -nE -e "$pattern" -- "$file")"; then
      echo "ERROR: potential secret pattern in $file (matched /$pattern/)" >&2
      echo "$matches" >&2
      FINDINGS=1
    fi
  done
done < <(find . -type f -print0)

if [[ "$FINDINGS" -ne 0 ]]; then
  echo "Secret pattern check failed. Remove secrets, rotate credentials, and retry." >&2
  exit 1
fi

echo "Secret pattern check passed."
