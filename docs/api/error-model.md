# API error model

Common error envelope for all Nova HTTP APIs. Stack traces and internal exception types are **never** returned to clients.

## Envelope

Every non-2xx JSON error response uses:

```json
{
  "error": {
    "code": "DOCUMENT_NOT_FOUND",
    "message": "No document exists for the given document_id.",
    "details": {
      "document_id": "doc_01HZX…"
    },
    "trace_id": "01J9TRACEEXAMPLE0000000000",
    "retryable": false
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | string | yes | Stable machine-readable code (`SCREAMING_SNAKE_CASE`) |
| `message` | string | yes | Safe, human-readable summary (no secrets, no stack traces) |
| `details` | object | no | Structured context (IDs, field names, constraint hints). Never include raw document bodies, credentials, or provider keys |
| `trace_id` | string | yes | Correlation ID for logs/traces (`REQ-OBS-001`, `REQ-OBS-002`) |
| `retryable` | boolean | yes | Whether a well-behaved client may retry the **same** request |

`Content-Type: application/json` for error bodies unless the client requested an unsupported media type before negotiation failed.

## HTTP status mapping

| HTTP | Meaning | Typical `code` values | `retryable` default |
|------|---------|----------------------|---------------------|
| **400** | Malformed request (bad JSON, missing required header/body field that is not schema-field validation) | `BAD_REQUEST`, `INVALID_CONTENT_TYPE`, `MISSING_IDEMPOTENCY_KEY` | `false` |
| **401** | Missing or invalid authentication | `UNAUTHENTICATED`, `INVALID_API_KEY` | `false` |
| **403** | Authenticated but not allowed | `FORBIDDEN`, `CUSTOMER_SCOPE_DENIED` | `false` |
| **404** | Resource does not exist (or is not visible to the caller) | `DOCUMENT_NOT_FOUND`, `SHIPMENT_NOT_FOUND`, `VALIDATION_NOT_FOUND`, `DECISION_NOT_FOUND` | `false` |
| **409** | Conflict with current state (duplicate non-idempotent create, incompatible lifecycle) | `CONFLICT`, `IDEMPOTENCY_KEY_REUSE_MISMATCH`, `RUN_ALREADY_TERMINAL` | `false` |
| **422** | Semantically invalid but well-formed request (schema/business validation) | `VALIDATION_FAILED`, `UNSUPPORTED_DOCUMENT_TYPE`, `PAYLOAD_TOO_LARGE`, `UNSUPPORTED_QUERY_INTENT` | `false` |
| **429** | Rate limited | `RATE_LIMITED` | `true` (after `Retry-After`) |
| **500** | Unexpected server failure | `INTERNAL_ERROR` | `false` (or `true` only when ops explicitly marks the failure class as safe to retry) |
| **502** | Upstream dependency returned an invalid/failed response (e.g. LLM provider) | `UPSTREAM_ERROR`, `AI_PROVIDER_ERROR` | `true` when transient; else `false` |
| **503** | Service temporarily unavailable (not ready, dependency down, maintenance) | `SERVICE_UNAVAILABLE`, `DEPENDENCY_UNAVAILABLE` | `true` |

### Notes on status choice

- Prefer **422** over **400** for Pydantic/schema field errors once the body parsed as JSON.
- Prefer **404** over **403** when revealing existence would leak another tenant’s IDs is **not** a concern for Part 1 single-tenant demos; for multi-tenant later, prefer opaque **404** for cross-tenant access.
- Ingestion that is accepted but still processing is **not** an error — use **202** with a run status (see [contracts.md](./contracts.md)).

## Application error classes → HTTP

Aligns with Phase 2 architecture error taxonomy (names are logical; HTTP mapping is normative for the public API):

| Logical class | HTTP | Example `code` | `retryable` |
|---------------|------|----------------|-------------|
| Request validation | 422 | `VALIDATION_FAILED` | false |
| Document processing (client-fixable) | 422 | `UNSUPPORTED_MEDIA_TYPE`, `DOCUMENT_UNREADABLE` | false |
| Not found | 404 | `*_NOT_FOUND` | false |
| Conflict / idempotency mismatch | 409 | `IDEMPOTENCY_KEY_REUSE_MISMATCH` | false |
| Authentication | 401 | `UNAUTHENTICATED` | false |
| Authorization | 403 | `FORBIDDEN` | false |
| AI provider transient | 502 | `AI_PROVIDER_ERROR` | true |
| AI output schema failure (after retries) | 422 or 502* | `AI_OUTPUT_INVALID` | false |
| Timeout | 504† or 502 | `TIMEOUT` | true if safe |
| Retry exhausted | 502 / 503 | `RETRY_EXHAUSTED` | false |
| Persistence | 500 / 503 | `PERSISTENCE_ERROR` | false / true if connection blip |
| Rate limit | 429 | `RATE_LIMITED` | true |

\* Prefer failing the **run** into a safe terminal disposition (`HUMAN_REVIEW` / halt) rather than returning 502 to a later GET; GETs return persisted state.  
† Part 1 may map request-timeouts to **504** if the gateway supports it; otherwise **502** with `code=TIMEOUT`.

## Security constraints

- Never include stack traces, file paths on the server, SQL, raw prompts, or API keys in `message` or `details`.
- Redact authorization headers in logs (`docs/security/baseline.md`).
- Prefer IDs and hashes over document payloads in `details`.

## Client guidance

1. Branch on `error.code`, not on substring matching `message`.
2. Retry only when `retryable=true`, respecting `Retry-After` when present.
3. Always log/store `trace_id` when filing an incident.

## Related

- [contracts.md](./contracts.md)
- [idempotency.md](./idempotency.md)
- [query-interface.md](./query-interface.md)
- Requirements: `REQ-OBS-004`, `REQ-SEC-003`, `REQ-EXT-006`
