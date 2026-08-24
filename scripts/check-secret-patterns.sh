#!/usr/bin/env bash
# Scan repository text files for high-confidence secret patterns.
# Intentionally conservative to avoid noisy false positives on documentation.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "== Nova secret pattern check =="

# Tracked + untracked (non-ignored) files so local pre-commit runs are meaningful
mapfile -t files < <(git ls-files -c -o --exclude-standard)

if [[ "${#files[@]}" -eq 0 ]]; then
  echo "No files; nothing to scan."
  exit 0
fi

patterns=(
  'AKIA[0-9A-Z]{16}'
  'BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY'
  'ghp_[A-Za-z0-9]{36}'
  'github_pat_[A-Za-z0-9_]{20,}'
  'xox[baprs]-[A-Za-z0-9-]{10,}'
  'sk-proj-[A-Za-z0-9_-]{20,}'
  'OPENAI_API_KEY[[:space:]]*=[[:space:]]*['\''\"]?sk-'
  'ANTHROPIC_API_KEY[[:space:]]*=[[:space:]]*['\''\"]?sk-'
)

# OpenAI-style keys: require sk- followed by a long token, but skip markdown discussion lines
# that only mention the prefix in docs. We still catch assignment-style leaks via env assignments above
# and the sk-proj pattern. Broader sk- scan:
sk_pattern='(^|[^A-Za-z0-9])sk-[A-Za-z0-9]{32,}'

fail=0
scan_file() {
  local file="$1"
  local pattern="$2"
  # Skip binary-ish files
  if ! grep -Iqe . "$file" 2>/dev/null; then
    return 0
  fi
  if grep -nE "$pattern" "$file" >/tmp/nova-secret-match.$$ 2>/dev/null; then
    if [[ -s /tmp/nova-secret-match.$$ ]]; then
      echo "POTENTIAL SECRET MATCH in $file for pattern: $pattern" >&2
      cat /tmp/nova-secret-match.$$ >&2
      fail=1
    fi
  fi
  rm -f /tmp/nova-secret-match.$$
}

for file in "${files[@]}"; do
  [[ -f "$file" ]] || continue
  for pattern in "${patterns[@]}"; do
    scan_file "$file" "$pattern"
  done
  scan_file "$file" "$sk_pattern"
done

tracked_env="$(printf '%s\n' "${files[@]}" | grep -E '(^|/)\.env($|\.)' | grep -v '\.example$' || true)"
if [[ -n "$tracked_env" ]]; then
  echo "Tracked/present .env files are not allowed:" >&2
  echo "$tracked_env" >&2
  fail=1
fi

if [[ "$fail" -ne 0 ]]; then
  echo "Secret pattern check FAILED" >&2
  exit 1
fi

echo "Secret pattern check PASSED"
