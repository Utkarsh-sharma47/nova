#!/usr/bin/env bash
# Phase 1: verify repository documentation / foundation files exist.
# Fails loudly on missing required files. Does not invent application checks.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

REQUIRED_FILES=(
  "README.md"
  "CONTRIBUTING.md"
  "DEVELOPMENT.md"
  "SECURITY.md"
  ".gitignore"
  ".env.example"
  ".github/workflows/ci.yml"
  "docs/deployment/ci-cd.md"
  "scripts/check-docs-structure.sh"
  "scripts/check-secret-patterns.sh"
)

MISSING=0

echo "==> Checking required Phase 1 foundation files"

for path in "${REQUIRED_FILES[@]}"; do
  if [[ ! -e "$path" ]]; then
    echo "ERROR: missing required file: $path" >&2
    MISSING=1
  else
    echo "OK: $path"
  fi
done

if [[ ! -s ".env.example" ]]; then
  echo "ERROR: .env.example must be non-empty" >&2
  MISSING=1
fi

if ! grep -qE '^\.env$' .gitignore && ! grep -qE '^\*\.env$' .gitignore; then
  echo "ERROR: .gitignore must ignore .env or *.env" >&2
  MISSING=1
fi

if grep -qE '(API_KEY|SECRET|PASSWORD|TOKEN)=.{8,}' .env.example; then
  # Allow commented placeholders; fail on uncommented long secret-looking assignments.
  if grep -vE '^\s*#' .env.example | grep -qE '(API_KEY|SECRET|PASSWORD|TOKEN)=.{8,}'; then
    echo "ERROR: .env.example appears to contain real-looking secret values" >&2
    MISSING=1
  fi
fi

if [[ "$MISSING" -ne 0 ]]; then
  echo "Docs/structure check failed." >&2
  exit 1
fi

echo "Docs/structure check passed."
