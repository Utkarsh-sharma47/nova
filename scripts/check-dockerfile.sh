#!/usr/bin/env bash
# Structural checks for the production Dockerfile (no secrets, non-root, healthcheck).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FILE="$ROOT/Dockerfile"

echo "== Dockerfile structural check =="

fail=0
require_grep() {
  local pattern="$1"
  local label="$2"
  if ! grep -Eq "$pattern" "$FILE"; then
    echo "MISSING: $label ($pattern)" >&2
    fail=1
  else
    echo "OK: $label"
  fi
}

forbid_grep() {
  local pattern="$1"
  local label="$2"
  if grep -Eq "$pattern" "$FILE"; then
    echo "FORBIDDEN: $label ($pattern)" >&2
    fail=1
  else
    echo "OK: absent $label"
  fi
}

require_grep '^FROM python:3\.12-slim' 'python 3.12 slim base'
require_grep '^USER nova' 'non-root user'
require_grep '^HEALTHCHECK' 'HEALTHCHECK instruction'
require_grep 'entrypoint\.sh' 'entrypoint for migrations/signals'
forbid_grep 'API_AUTH_TOKEN=.+' 'hardcoded API token'
forbid_grep 'LLM_API_KEY=.+' 'hardcoded LLM key'
forbid_grep 'COPY +\.env' 'copying .env into image'
forbid_grep 'PASSWORD=.+' 'hardcoded password assignment'

if [[ "$fail" -ne 0 ]]; then
  echo "Dockerfile check FAILED" >&2
  exit 1
fi

echo "Dockerfile check PASSED"
