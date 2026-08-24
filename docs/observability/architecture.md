# Observability architecture

Extends [philosophy.md](./philosophy.md). ADR: [0007](../decisions/0007-observability.md).

Detail: [logging.md](./logging.md), [metrics.md](./metrics.md).

## Identifiers

| ID | Scope |
|----|-------|
| `request_id` | Inbound HTTP request (`X-Request-ID`) |
| `trace_id` | Full verification run (`X-Trace-ID`; defaults to request id) |
| `agent_execution_id` | One agent invocation (reserved for agent phases) |

## Structured log fields (minimum)

`timestamp`, `level`, `service`, `environment`, `message`, `event`, `trace_id`, `request_id`, `duration_ms`, `status`, plus HTTP `path`/`method`/`http_status` when applicable.

## Metrics (implemented baseline)

Library: **`prometheus_client`** → `GET /metrics`.

`nova_http_requests_total`, `nova_http_request_latency_seconds`, `nova_http_errors_total`, plus document ingestion/processing counters (ready for later wiring).

## Health

- `GET /health` — liveness (no dependency checks)
- `GET /ready` — database reachable **and** `schema_meta` bootstrap row present
