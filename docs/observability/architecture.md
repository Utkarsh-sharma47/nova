# Observability architecture

Extends [philosophy.md](./philosophy.md). ADR: [0007](../decisions/0007-observability.md). Phase 11 confirms identifiers, metrics, and health for the runnable Part 1 stack.

## Identifiers

| ID | Scope |
|----|-------|
| `request_id` | Inbound HTTP request (`X-Request-Id` in/out) |
| `trace_id` | Correlation across the verification path (`X-Trace-Id` in/out) |
| `run_id` | Verification run / pipeline orchestration |
| `agent_execution_id` | One agent invocation (extractor / validator / router) |

Clients may supply `X-Request-Id` / `X-Trace-Id`; otherwise the API generates them. Responses always echo both headers.

## Structured logs

JSON on stdout. Field reference: [logging.md](./logging.md).

Useful event classes (never include document bodies or secrets):

| Area | Examples |
|------|----------|
| HTTP | `http.request`, `http.unhandled_error` |
| App | `app.start` |
| Upload / ingest | document accepted / rejected with codes |
| Pipeline | stage start/complete/fail with `run_id`, `stage`, `status`, `duration_ms` |
| Agents | execution metadata + `agent_execution_id` |
| Query | intent name, status, `customer_id`, latency |
| Failure | stable `error_code`, retryable flag |

## Metrics

Prometheus exposition at `GET /metrics` (also proxied via Compose `web`).

Implemented low-cardinality HTTP series:

- `nova_http_requests_total{method,path,status}`
- `nova_http_request_latency_seconds{method,path}`

Paths are normalized (e.g. `/v1/documents/{document_id}`) to avoid cardinality explosions.

Additional agent/LLM counters remain defined for calibration as stages emit them; do not invent SLO numbers in docs.

## Health

| Endpoint | Meaning |
|----------|---------|
| `GET /health` | Process liveness |
| `GET /ready` | DB connectivity + required tables + storage readiness |
| `GET /metrics` | Prometheus scrape |

Unauthenticated by design for operator probes behind a trusted network / reverse proxy.

## Related

- [logging.md](./logging.md)
- [../deployment/production.md](../deployment/production.md)
- [../operations/recovery.md](../operations/recovery.md)
