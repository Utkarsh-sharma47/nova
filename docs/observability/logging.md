# Runtime logging

Nova emits one JSON object per request completion. Stable fields include
`timestamp`, `level`, `service`, `environment`, `trace_id`, `request_id`,
`event`, `duration_ms`, and `status`. Responses propagate `X-Request-Id` and
`X-Trace-Id`; clients may supply either header.

Authorization, API keys, tokens, cookies, database URLs, and document contents
must never be included. Error responses expose a safe trace ID and stable code,
not stack traces or internal paths. Phase 3 does not configure an external
OpenTelemetry exporter or metrics backend.
