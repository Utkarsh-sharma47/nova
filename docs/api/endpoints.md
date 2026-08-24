# API endpoint specifications

Complement to [contracts.md](./contracts.md) and [surface.md](./surface.md).

## POST `/v1/documents`

Ingest into a shipment (create if needed). Phase 3 accepts exactly one multipart
file or a relative pre-staged `source_path` beneath `DOCUMENT_STORAGE_PATH`.
`Idempotency-Key` and API authentication are required. Response is
`202 Accepted` with document, shipment, run, replay, and trace fields. Errors:
400/401/404/409/413/422. Audit events are not yet implemented.

## GET `/v1/documents/{document_id}`

Metadata + latest extraction summary. `404` if missing. Optional `version_id` query.

## GET `/v1/shipments/{shipment_id}`

Shipment state, document IDs, latest decision summary.

## GET `/v1/documents/{document_id}/validation`

Deferred. No Phase 3 route exists; the planned contract is a latest
`ValidationResult` DTO with optional historical lookup.

## GET `/v1/documents/{document_id}/decision`

Deferred. No Phase 3 route exists; the planned contract returns the latest
`DecisionResult` DTO. Part 2 may add approval fields.

## POST `/v1/query`

Deferred. No Phase 3 route exists. The planned grounded query contract is
documented in [query-interface.md](./query-interface.md).

## GET `/health` / `/ready` / `/metrics`

Liveness, database-schema/storage readiness, and Prometheus metrics. No auth.
