# Part 1 API contracts

HTTP API contracts for Nova Part 1. Phase 3 implements authenticated document
ingestion, document/shipment retrieval, health, readiness, and metrics. Other
sections are forward contracts and are explicitly marked as deferred.

Aligned with:

- Requirements: `REQ-EXT-001`, `REQ-DATA-*`, `REQ-QUERY-*`, `REQ-OBS-*`, `REQ-SEC-*`, `REQ-ROUTER-*`, `REQ-VAL-*`
- Architecture: ingestion → extraction → validation → routing → persistence → query/UI
- Stack intent: FastAPI + Pydantic ([ADR-0004](../decisions/0004-api-framework.md), [ADR-0002](../decisions/0002-backend-stack.md)) when those ADRs are merged

Cross-cutting docs: [versioning.md](./versioning.md) · [error-model.md](./error-model.md) · [idempotency.md](./idempotency.md) · [query-interface.md](./query-interface.md)

---

## Conventions

| Topic | Rule |
|-------|------|
| Base path | `/v1` for resource APIs; `/health` and `/ready` unversioned |
| IDs | Opaque string IDs (UUID-based recommended), e.g. `doc_…`, `shp_…` |
| Time | ISO-8601 UTC |
| Errors | [error-model.md](./error-model.md) |
| Auth (Part 1 assumption) | Single shared **API key** via `Authorization: Bearer <token>` or `X-API-Key` for demo; not a full RBAC matrix |
| Content | JSON except ingestion upload (`multipart/form-data`) |
| Trace | Every response should expose `trace_id` (body and/or `X-Trace-Id` header). Pipeline entities also carry `run_id` |

### Shared enums (wire values)

| Enum | Values |
|------|--------|
| Document processing status | `ACCEPTED`, `PROCESSING`, `EXTRACTED`, `VALIDATED`, `DECIDED`, `FAILED` |
| Validation outcome | `MATCH`, `MISMATCH`, `UNCERTAIN` |
| Router decision | `AUTO_APPROVE`, `HUMAN_REVIEW`, `AMENDMENT_REQUEST` |

---

## 1. Document ingestion

Register a trade/shipping document and start (or enqueue) a verification run.

| | |
|--|--|
| **Method** | `POST` |
| **Path** | `/v1/documents` |
| **Auth** | Required (API key) |
| **Idempotency** | **Required** `Idempotency-Key` — see [idempotency.md](./idempotency.md) |

### Request

`Content-Type: multipart/form-data`

| Part / field | Required | Description |
|--------------|----------|-------------|
| `file` | one of `file` or `source_path` | Document bytes (PDF/image/etc. allow-list enforced at implementation) |
| `source_path` | one of `file` or `source_path` | Server-local or pre-staged path for demos (ingestion port abstraction) |
| `customer_id` | yes | Customer whose rules apply |
| `shipment_id` | no | Attach to existing shipment; if omitted, create a new shipment (1:N ready) |
| `document_type` | no | Hint: `INVOICE`, `BILL_OF_LADING`, `OTHER`, `UNKNOWN` |
| `external_ref` | no | Caller reference for domain-level dedupe |

Headers:

| Header | Required |
|--------|----------|
| `Idempotency-Key` | yes |
| `Authorization` / `X-API-Key` | yes |
| `X-Request-Id` | no (client); server always assigns `trace_id` |

### Response — `202 Accepted`

```json
{
  "document_id": "doc_…",
  "shipment_id": "shp_…",
  "run_id": "run_…",
  "status": "ACCEPTED",
  "idempotent_replay": false,
  "trace_id": "01J9…"
}
```

Phase 3 stores normalized document content and creates a queued verification
run. Extractor, Validator, and Router execution is deferred; clients can
retrieve the accepted document and shipment metadata.

### Status codes

| Code | When |
|------|------|
| 202 | Accepted (new or idempotent replay of successful accept) |
| 400 | Missing idempotency key / bad multipart |
| 401 / 403 | Auth |
| 409 | Idempotency key reuse mismatch / external_ref conflict |
| 413 | Payload too large (may also be 422 with `PAYLOAD_TOO_LARGE`) |
| 422 | Unsupported type, validation of fields |
| 429 | Rate limited |
| 503 | Not ready / dependency unavailable |

### Validation

- Exactly one of `file` or `source_path`
- File size/type allow-list (`REQ-SEC-004` when enabled)
- `customer_id` present and authorized

### Observability

Log `trace_id`, `run_id`, `document_id`, `shipment_id`, `customer_id`, `idempotency_replay`, content hash — not raw bytes.

### Security assumptions

- Authenticated operator/service only
- Documents treated as sensitive commercial data
- Upload malware scanning strategy deferred but size/type limits apply when implemented

### Part 2 extension

Same ingestion port can be invoked by email/file adapters without changing this HTTP shape; additional metadata fields may be added optionally under `/v1`.

---

## 2. Document retrieval

| | |
|--|--|
| **Method** | `GET` |
| **Path** | `/v1/documents/{document_id}` |
| **Auth** | Required |
| **Idempotency** | N/A (safe GET) |

### Request

Path param: `document_id`.  
Optional query: `include=extraction` to embed latest extraction summary (confidence/evidence references).

### Response — `200 OK`

```json
{
  "document_id": "doc_…",
  "shipment_id": "shp_…",
  "customer_id": "cust_…",
  "document_type": "BILL_OF_LADING",
  "status": "DECIDED",
  "run_id": "run_…",
  "created_at": "2026-08-25T00:00:00Z",
  "updated_at": "2026-08-25T00:05:00Z",
  "content": {
    "media_type": "application/pdf",
    "size_bytes": 204800,
    "content_sha256": "…",
    "download_url": null
  },
  "extraction": null,
  "links": {
    "validation": "/v1/documents/doc_…/validation",
    "decision": "/v1/documents/doc_…/decision",
    "shipment": "/v1/shipments/shp_…"
  },
  "trace_id": "01J9…"
}
```

When `include=extraction` and extraction exists, `extraction` contains field list with `name`, `value`, `presence`, `confidence`, `uncertainty`, and evidence refs (aligned with agent contracts). Raw model dumps are not required on this endpoint.

### Status codes

| Code | When |
|------|------|
| 200 | Found |
| 401 / 403 | Auth |
| 404 | Unknown / not visible |
| 500 / 503 | Server / dependency |

### Validation

- `document_id` path format; unknown → 404

### Observability

Log access with `trace_id` + `document_id` (no content body at info level).

### Security assumptions

- Caller scoped to customer ownership
- `download_url` optional and short-lived if introduced; default Part 1 may omit binary download

---

## 3. Shipment retrieval

| | |
|--|--|
| **Method** | `GET` |
| **Path** | `/v1/shipments/{shipment_id}` |
| **Auth** | Required |
| **Idempotency** | N/A |

### Response — `200 OK`

```json
{
  "shipment_id": "shp_…",
  "customer_id": "cust_…",
  "status": "OPEN",
  "document_ids": ["doc_…"],
  "documents": [
    {
      "document_id": "doc_…",
      "document_type": "INVOICE",
      "status": "DECIDED",
      "run_id": "run_…"
    }
  ],
  "latest_decision": {
    "document_id": "doc_…",
    "decision": "HUMAN_REVIEW"
  },
  "created_at": "2026-08-25T00:00:00Z",
  "updated_at": "2026-08-25T00:05:00Z",
  "trace_id": "01J9…"
}
```

`documents` is an array even when Part 1 typically has one entry (`REQ-DATA-002`).

### Status codes

200, 401, 403, 404, 500, 503 — same pattern as document GET.

### Observability / security

Same as document retrieval; shipment aggregates must not leak cross-customer documents.

---

## 4. Validation results

| | |
|--|--|
| **Method** | `GET` |
| **Path** | `/v1/documents/{document_id}/validation` |
| **Auth** | Required |
| **Idempotency** | N/A |

Alternate (optional): `GET /v1/validations/{validation_id}` once IDs are advertised in links.

### Response — `200 OK`

```json
{
  "validation_id": "val_…",
  "document_id": "doc_…",
  "shipment_id": "shp_…",
  "run_id": "run_…",
  "overall_result": "MISMATCH",
  "checks": [
    {
      "check_id": "chk_…",
      "rule_id": "rule_consignee_match",
      "field_name": "consignee_name",
      "result": "MISMATCH",
      "reason": "Extracted consignee does not match customer allow-list.",
      "expected": { "type": "allow_list_ref", "ref": "…" },
      "actual": { "value": "…", "confidence": 0.62 },
      "evidence_ids": ["ev_…"]
    }
  ],
  "created_at": "2026-08-25T00:04:00Z",
  "trace_id": "01J9…"
}
```

`overall_result` ∈ `MATCH` | `MISMATCH` | `UNCERTAIN`.

### Status codes

| Code | When |
|------|------|
| 200 | Validation record exists |
| 404 | Document missing **or** validation not yet available |
| 409 | Optional: document `FAILED` before validation (or return 404 with `VALIDATION_NOT_FOUND`) |

Part 1 recommendation: if still `PROCESSING`, return **404** `VALIDATION_NOT_FOUND` with `details.status=PROCESSING` **or** **409** `RUN_NOT_READY` — pick one in implementation and keep it stable; prefer **404** with `retryable=true` only if short-lived, else clients poll document `status`.

### Validation / observability / security

- Auditable rule IDs required (`REQ-VAL-006`)
- Do not expose stack traces from rule engine failures; persist structured check errors instead

---

## 5. Decision results

| | |
|--|--|
| **Method** | `GET` |
| **Path** | `/v1/documents/{document_id}/decision` |
| **Auth** | Required |
| **Idempotency** | N/A |

### Response — `200 OK`

```json
{
  "decision_id": "dec_…",
  "document_id": "doc_…",
  "shipment_id": "shp_…",
  "run_id": "run_…",
  "decision": "HUMAN_REVIEW",
  "rationale": "Validation UNCERTAIN on consignee; confidence below policy.",
  "policy_version": "routing-policy-1",
  "inputs": {
    "overall_validation": "UNCERTAIN",
    "min_field_confidence": 0.41
  },
  "created_at": "2026-08-25T00:04:30Z",
  "approval_state": "NONE",
  "trace_id": "01J9…"
}
```

`decision` ∈ `AUTO_APPROVE` | `HUMAN_REVIEW` | `AMENDMENT_REQUEST`.

`approval_state` is reserved for Part 2 human approval (`NONE` in Part 1). Router output is not overwritten in place.

### Status codes

Same readiness pattern as validation GET (200 when decided; 404 while pending).

### Security / observability

- Fail-safe: never imply `AUTO_APPROVE` on incomplete runs
- Log decision reads with `run_id` for audit linkage

---

## 6. Natural-language query

| | |
|--|--|
| **Method** | `POST` |
| **Path** | `/v1/query` |
| **Auth** | Required |
| **Idempotency** | Not required (read-only); see [query-interface.md](./query-interface.md) |

Full request/response, intent allow-list, unsupported/failure distinction, and **no arbitrary LLM SQL** rule: [query-interface.md](./query-interface.md).

### Status codes (summary)

| Code | When |
|------|------|
| 200 | Contract body with `status` ∈ `RESULT` \| `EMPTY` \| `UNSUPPORTED` \| `FAILURE` |
| 400 / 422 | Malformed question payload |
| 401 / 403 | Auth |
| 429 | Rate limited |
| 502 / 503 | Transport-level dependency failure |

---

## 7. Health (liveness)

| | |
|--|--|
| **Method** | `GET` |
| **Path** | `/health` |
| **Auth** | None (orchestrators) |
| **Idempotency** | N/A |

### Response — `200 OK`

```json
{
  "status": "ok"
}
```

Indicates the API process is alive. **Does not** check database or LLM provider.

### Status codes

| Code | When |
|------|------|
| 200 | Process up |
| 503 | Process intentionally refusing traffic (rare) |

### Observability / security

- No secrets; minimal body
- Do not bind heavy dependency checks here (avoid false kill loops)

---

## 8. Readiness

| | |
|--|--|
| **Method** | `GET` |
| **Path** | `/ready` |
| **Auth** | None (orchestrators) |
| **Idempotency** | N/A |

### Response — `200 OK`

```json
{
  "status": "ready",
  "checks": {
    "database": "ok",
    "object_storage": "ok"
  }
}
```

### Response — `503 Service Unavailable`

```json
{
  "status": "not_ready",
  "checks": {
    "database": "fail",
    "object_storage": "ok"
  },
  "error": {
    "code": "DEPENDENCY_UNAVAILABLE",
    "message": "Database is not reachable.",
    "details": { "check": "database" },
    "trace_id": "01J9…",
    "retryable": true
  }
}
```

LLM provider reachability is **not** required for readiness in Part 1 (ingest may still accept and fail runs safely). Database availability **is** required.

### Validation

- None from clients

### Observability

Emit metrics on ready/not_ready transitions; include `trace_id` on 503.

### Security assumptions

- Unauthenticated but non-sensitive; do not expose internal hostnames, connection strings, or stack traces in `checks`

---

## Endpoint index

| Area | Method | Path |
|------|--------|------|
| Ingestion | `POST` | `/v1/documents` |
| Document retrieval | `GET` | `/v1/documents/{document_id}` |
| Shipment retrieval | `GET` | `/v1/shipments/{shipment_id}` |
| Validation results | `GET` | `/v1/documents/{document_id}/validation` |
| Decision results | `GET` | `/v1/documents/{document_id}/decision` |
| NL query | `POST` | `/v1/query` |
| Health | `GET` | `/health` |
| Readiness | `GET` | `/ready` |

## Explicitly out of Part 1 API surface

- Human approval actions / outbound send
- Email webhook ingestion (adapter may call the same domain ingestion port)
- Arbitrary admin SQL
- Agent debug prompts as public endpoints

## Related

- [README.md](./README.md)
- Agent I/O: `docs/agents/` (contracts when present)
- Domain persistence: `docs/database/`
- Architecture: [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md)
