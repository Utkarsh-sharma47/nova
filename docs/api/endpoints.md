# API endpoint specifications

Complement to [contracts.md](./contracts.md) and [surface.md](./surface.md).

## POST `/v1/documents`

Ingest into a shipment (create if needed). Multipart or JSON+storage ref. Headers: optional `Idempotency-Key`. Response `201` with ids + `trace_id`. Errors: 401/403/409/413/422. Audit: `DOCUMENT_INGESTED`. Extension: source metadata (`upload`/`email`/`api`).

## GET `/v1/documents/{document_id}`

Metadata + latest extraction summary. `404` if missing. Optional `version_id` query.

## GET `/v1/shipments/{shipment_id}`

Shipment state, document IDs, latest decision summary.

## GET `/v1/documents/{document_id}/validation`

Latest `ValidationResult` DTO; historical via `?validation_id=`.

## GET `/v1/documents/{document_id}/decision`

Latest `DecisionResult` DTO. Part 2 may add approval fields.

## POST `/v1/query`

`{ question, shipment_id?, document_id? }` → `{ answer, citations[], refused, trace_id }`. Must refuse when ungrounded ([query-interface.md](./query-interface.md)).

## GET `/health` / `/ready`

Liveness vs DB/config readiness. No auth.
