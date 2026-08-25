#!/usr/bin/env bash
# End-to-end Compose verification for Phase 3 foundation.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-nova_verify}"
API_PORT="${API_PORT:-8000}"
API_URL="${API_URL:-http://127.0.0.1:${API_PORT}}"

cleanup() {
  docker compose down -v --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "== ensure .env =="
if [[ ! -f .env ]]; then
  cp .env.example .env
  # Local verify token must not be the placeholder rejected by Settings.validate_runtime.
  if grep -q 'API_AUTH_TOKEN=replace-with-a-long-random-token' .env; then
    sed -i 's/API_AUTH_TOKEN=replace-with-a-long-random-token/API_AUTH_TOKEN=nova-local-verify-token-32chars/' .env
  fi
  if grep -q 'POSTGRES_PASSWORD=replace-me' .env; then
    sed -i 's/POSTGRES_PASSWORD=replace-me/POSTGRES_PASSWORD=nova/' .env
  fi
  echo "Created .env from .env.example (local verify placeholders substituted)"
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

echo "== basic authenticated ingest =="
TOKEN="$(grep -E '^API_AUTH_TOKEN=' .env | cut -d= -f2-)"
CUSTOMER_ID="$(
  docker compose exec -T db psql -U nova -d nova -Atc \
    "INSERT INTO customers (customer_id, name, status) VALUES (gen_random_uuid(), 'verify', 'active') RETURNING customer_id;" \
  | head -n 1 | tr -d '[:space:]'
)"
if [[ -z "${CUSTOMER_ID}" ]]; then
  CUSTOMER_ID="$(
    docker compose exec -T db psql -U nova -d nova -Atc \
      "SELECT customer_id FROM customers WHERE status='active' LIMIT 1;" \
    | head -n 1 | tr -d '[:space:]'
  )"
fi
INGEST_STATUS="$(
  curl -sS -o /tmp/nova_ingest.json -w '%{http_code}' \
    -X POST "$API_URL/v1/documents" \
    -H "X-API-Key: ${TOKEN}" \
    -H "Idempotency-Key: verify-compose-key-001" \
    -F "customer_id=${CUSTOMER_ID}" \
    -F "document_type=INVOICE" \
    -F "file=@<(echo -n invoice-42);filename=invoice.txt;type=text/plain" \
    2>/dev/null || true
)"
# Fallback without process substitution (more portable)
if [[ "${INGEST_STATUS}" != "202" ]]; then
  printf 'invoice number 42' >/tmp/nova_verify_invoice.txt
  INGEST_STATUS="$(
    curl -sS -o /tmp/nova_ingest.json -w '%{http_code}' \
      -X POST "$API_URL/v1/documents" \
      -H "X-API-Key: ${TOKEN}" \
      -H "Idempotency-Key: verify-compose-key-001" \
      -F "customer_id=${CUSTOMER_ID}" \
      -F "document_type=INVOICE" \
      -F "file=@/tmp/nova_verify_invoice.txt;type=text/plain"
  )"
fi
echo "ingest HTTP ${INGEST_STATUS}: $(cat /tmp/nova_ingest.json)"
test "${INGEST_STATUS}" = "202"

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
