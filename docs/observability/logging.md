# Structured logging

## Schema (stable fields)

Every request-scoped log line SHOULD include:

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | ISO-8601 UTC | Event time |
| `level` | string | DEBUG/INFO/WARNING/ERROR |
| `service` | string | e.g. `nova-api` |
| `environment` | string | local/test/ci/demo/production |
| `trace_id` | string | End-to-end verification correlation |
| `request_id` | string | Inbound HTTP request id |
| `event` | string | Stable event name (`http.request`, `app.start`, …) |
| `message` | string | Human-readable summary |
| `duration_ms` | number | Latency when applicable |
| `status` | string | `ok` / `error` (or domain status) |
| `path` / `method` / `http_status` | mixed | HTTP context |
| `error_type` / `error_code` | string | Failure taxonomy when present |

Optional later fields (agents): `agent_execution_id`, `document_id`, `shipment_id`, `stage`.

## Propagation

- Accept `X-Request-ID` / `X-Correlation-ID` and `X-Trace-ID` when provided.
- Otherwise generate UUIDs; default `trace_id = request_id` for single-request runs.
- Echo both IDs on response headers.

## Redaction

Never log: API keys, passwords, `Authorization`, cookies, full `DATABASE_URL`, document bodies, or raw extraction text. Secret-like keys in `extra_fields` are replaced with `[REDACTED]`.

## Implementation

- Package: `nova.observability`
- Middleware: `ObservabilityMiddleware`
- Format: JSON to stdout (Compose/log drivers collect it)

ADR: [0007](../decisions/0007-observability.md).
