#!/usr/bin/env bash
# End-to-end Compose verification for Phase 3 ops foundation.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-nova_verify}"
API_URL="${API_URL:-http://127.0.0.1:8000}"

cleanup() {
  docker compose down -v --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "== ensure .env =="
if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

echo "== docker compose up --build =="
docker compose up --build -d

echo "== wait for /health =="
deadline=$((SECONDS + 120))
until curl -fsS "$API_URL/health" >/dev/null 2>&1; do
  if (( SECONDS >= deadline )); then
    echo "API health check timed out" >&2
    docker compose logs api db >&2 || true
    exit 1
  fi
  sleep 2
done
echo "health OK: $(curl -fsS "$API_URL/health")"

echo "== wait for /ready (migrations applied) =="
deadline=$((SECONDS + 60))
until curl -fsS "$API_URL/ready" >/dev/null 2>&1; do
  if (( SECONDS >= deadline )); then
    echo "API readiness timed out" >&2
    docker compose logs api db >&2 || true
    exit 1
  fi
  sleep 2
done
echo "ready OK: $(curl -fsS "$API_URL/ready")"

echo "== metrics scrape =="
curl -fsS "$API_URL/metrics" | grep -q 'nova_http_requests_total'
echo "metrics OK"

echo "== restart api =="
docker compose restart api
deadline=$((SECONDS + 90))
until curl -fsS "$API_URL/health" >/dev/null 2>&1 && curl -fsS "$API_URL/ready" >/dev/null 2>&1; do
  if (( SECONDS >= deadline )); then
    echo "API did not recover after restart" >&2
    docker compose logs api >&2 || true
    exit 1
  fi
  sleep 2
done
echo "restart recovery OK"

echo "== compose verify PASSED =="
