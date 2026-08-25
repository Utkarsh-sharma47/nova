#!/usr/bin/env bash
# Compose smoke + recovery checks for Phase 11 production readiness.
# Does not perform remote/cloud deploy.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

API_PORT="${API_PORT:-18000}"
WEB_PORT="${WEB_PORT:-18080}"
POSTGRES_PORT="${POSTGRES_PORT:-15432}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-nova-p11-verify}"
export API_PORT WEB_PORT POSTGRES_PORT COMPOSE_PROJECT_NAME

API_BASE="http://127.0.0.1:${API_PORT}"
WEB_BASE="http://127.0.0.1:${WEB_PORT}"

if [[ ! -f .env ]]; then
  echo "verify-production-readiness: creating .env from .env.example" >&2
  cp .env.example .env
fi

python3 - <<'PY'
from pathlib import Path
import secrets
import re

path = Path(".env")
text = path.read_text() if path.exists() else ""
lines = text.splitlines()
changed = False

def set_or_replace(key: str, value: str, predicate) -> None:
    global lines, changed
    found = False
    out = []
    for line in lines:
        if line.startswith(f"{key}="):
            found = True
            current = line.split("=", 1)[1]
            if predicate(current):
                out.append(f"{key}={value}")
                changed = True
            else:
                out.append(line)
        else:
            out.append(line)
    if not found:
        out.append(f"{key}={value}")
        changed = True
    lines = out

weak_tokens = {
    "replace-with-a-long-random-token",
    "replace-me",
    "changeme",
    "your-api-key-here",
    "your-token-here",
    "",
}
set_or_replace(
    "API_AUTH_TOKEN",
    secrets.token_urlsafe(32),
    lambda v: v.strip() in weak_tokens,
)
set_or_replace(
    "POSTGRES_PASSWORD",
    secrets.token_urlsafe(24),
    lambda v: v.strip() in {"replace-me", "changeme", "nova", ""},
)
if changed:
    path.write_text("\n".join(lines) + "\n")
PY

cleanup() {
  docker compose -p "$COMPOSE_PROJECT_NAME" down --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "== Phase 11 production-readiness verify =="
echo "project=${COMPOSE_PROJECT_NAME} API_PORT=${API_PORT} WEB_PORT=${WEB_PORT} POSTGRES_PORT=${POSTGRES_PORT}"
echo "NOTE: remote deploy is NOT EXECUTED by this script."

docker compose -p "$COMPOSE_PROJECT_NAME" up --build -d

wait_http() {
  local url="$1"
  local name="$2"
  local attempts="${3:-60}"
  local i
  for ((i = 1; i <= attempts; i++)); do
    if curl -sf "$url" >/dev/null; then
      echo "OK: ${name}"
      return 0
    fi
    sleep 2
  done
  echo "FAIL: ${name} did not become ready (${url})" >&2
  docker compose -p "$COMPOSE_PROJECT_NAME" ps >&2 || true
  docker compose -p "$COMPOSE_PROJECT_NAME" logs --tail=80 api web db >&2 || true
  return 1
}

wait_http "${API_BASE}/health" "GET /health"
wait_http "${API_BASE}/ready" "GET /ready"
wait_http "${API_BASE}/metrics" "GET /metrics"
wait_http "${WEB_BASE}/" "GET web /"

echo "-- runtime-config (token not printed) --"
python3 - <<PY
import sys
import urllib.request

body = urllib.request.urlopen("${WEB_BASE}/runtime-config.js", timeout=10).read().decode()
if "__NOVA_RUNTIME__" not in body or "apiAuthToken" not in body:
    print("FAIL: runtime-config.js missing required keys", file=sys.stderr)
    raise SystemExit(1)
# Ensure a non-empty JSON string value exists without printing it.
marker = "apiAuthToken:"
idx = body.find(marker)
if idx < 0:
    raise SystemExit("FAIL: apiAuthToken missing")
tail = body[idx + len(marker) :].lstrip()
if not tail.startswith('"') or len(tail) < 3 or tail[1] == '"':
    print("FAIL: apiAuthToken appears empty", file=sys.stderr)
    raise SystemExit(1)
print("OK: runtime-config keys present (token redacted)")
PY

echo "-- alembic current --"
CURRENT="$(docker compose -p "$COMPOSE_PROJECT_NAME" exec -T api alembic current)"
echo "$CURRENT" | grep -q '0004_phase7_pipeline'
echo "OK: alembic current includes 0004_phase7_pipeline"

restart_and_check() {
  local service="$1"
  echo "-- restart ${service} --"
  docker compose -p "$COMPOSE_PROJECT_NAME" restart "$service"
  wait_http "${API_BASE}/health" "health after ${service} restart" 45
  wait_http "${API_BASE}/ready" "ready after ${service} restart" 45
  wait_http "${WEB_BASE}/" "web after ${service} restart" 45
}

restart_and_check api
restart_and_check db
restart_and_check web

echo "PASS: verify-production-readiness (local Compose only; remote deploy NOT EXECUTED)"
