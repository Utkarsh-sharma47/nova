# Runtime logging

Nova emits structured **JSON** log lines to stdout (one object per log record).

## Stable fields

| Field | Description |
|-------|-------------|
| `timestamp` | UTC ISO-8601 with `Z` |
| `level` | `DEBUG` / `INFO` / `WARNING` / `ERROR` / `CRITICAL` |
| `service` | From `SERVICE_NAME` (default `nova-api`) |
| `environment` | From `APP_ENV` |
| `trace_id` | Correlation ID |
| `request_id` | Per-request ID |
| `event` | Stable event name (e.g. `http.request`, `app.start`) |
| `message` | Human-readable summary |
| `duration_ms` | When applicable |
| `status` | e.g. `ok` / `error` |
| `path` / `method` / `http_status` | HTTP completion |
| `error_code` | Stable application code when set |
| `run_id` | Verification run |
| `agent_execution_id` | Agent invocation |
| `document_id` / `customer_id` | Entity refs (not payloads) |
| `stage` | Pipeline stage name when set |

Exception records may include `error_type` and `exception_present` without dumping stack traces to clients.

## Headers

Responses set `X-Request-Id` and `X-Trace-Id`. Clients may supply either header on ingress.

## Forbidden content

Authorization values, API keys, tokens, cookies, database URLs, and document contents must never appear in logs. The JSON formatter redacts secret-like field names.

API error envelopes expose a safe `trace_id` and stable `code` — not internal paths or stack traces.

## Related

- [architecture.md](./architecture.md)
- [../security/baseline.md](../security/baseline.md)
