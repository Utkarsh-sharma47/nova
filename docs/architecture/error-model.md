# Error model

Consistent application errors.

- **Typed contract:** `nova.contracts.errors.ErrorResponse` (`error_type`, `error_code`, `message`, `details`, `trace_id`, `request_id`, `retryable`).
- **HTTP envelope:** nested `{ "error": { "code", "message", … } }` per [`docs/api/error-model.md`](../api/error-model.md). The API edge maps `error_code` → `code` and always includes correlation IDs.

These two shapes are intentional: agents and internal stages speak `ErrorResponse`; public HTTP clients consume the stable envelope.

## Principles

- Machine-readable `error_code` / HTTP `code`
- Safe human `message` (no secrets, no raw provider payloads)
- Optional redacted `details`
- `trace_id` and `request_id` when available
- Explicit `retryable`
- HTTP mapping at API edge only

## Types

| Type | Code prefix | Retryable | HTTP |
|------|-------------|-----------|------|
| ValidationError | `VAL_` | no | 422 |
| DocumentProcessingError | `DOC_` | sometimes | 422/500 |
| AIProviderError → **502** |
| AIOutputError | `AI_OUTPUT_` | maybe once | 502 |
| TimeoutError | `TIMEOUT_` | maybe | 504 |
| RetryExhaustedError | `RETRY_` | no | 503 |
| PersistenceError | `DB_` | maybe | 503 |
| NotFoundError | `NOT_FOUND_` | no | 404 |
| ConflictError | `CONFLICT_` | no | 409 |
| AuthenticationError | `AUTHN_` | no | 401 |
| AuthorizationError | `AUTHZ_` | no | 403 |

## Forbidden

- Stack traces to clients
- Logging API keys or full document bodies on errors
- Mapping errors to `AUTO_APPROVE`
