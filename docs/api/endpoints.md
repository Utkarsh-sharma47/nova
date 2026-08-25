# API endpoint specifications

Complement to [contracts.md](./contracts.md) and [surface.md](./surface.md).

**Status (Part 1):** Implemented in `src/nova/api/routes/__init__.py`. Auth: `Authorization: Bearer` or `X-API-Key` on all `/v1/*` routes. Ops endpoints `/health`, `/ready`, `/metrics` are unauthenticated.

## POST `/v1/documents`

Ingest into a shipment (create if needed). Accepts exactly one multipart file or a relative pre-staged `source_path` beneath `DOCUMENT_STORAGE_PATH`. `Idempotency-Key` and API authentication are required. Response is `202 Accepted` with document, shipment, run, replay, and trace fields. Errors: `400` / `401` / `404` / `409` / `413` / `422` / `5xx`. Audit event table writes are **not** implemented (see known limitations).

## GET `/v1/documents`

List recent documents for the ops UI (pagination/limit query params as implemented).

## GET `/v1/documents/{document_id}`

Metadata + latest extraction summary. `404` if missing. Optional `version_id` query.

## GET `/v1/documents/{document_id}/validation`

Latest `ValidationResult` for the document. `404` if no validation yet.

## GET `/v1/documents/{document_id}/decision`

Latest `DecisionResult` for the document. `404` if no decision yet. Part 2 may add human-approval fields without rewriting history.

## GET `/v1/shipments/{shipment_id}`

Shipment state, document IDs, latest decision summary.

## GET `/v1/shipments/{shipment_id}/validation`

Alias: latest document validation under the shipment. `404` if unavailable.

## GET `/v1/shipments/{shipment_id}/decision`

Alias: latest document decision under the shipment. `404` if unavailable.

## POST `/v1/customers`

Create a demo/ops customer record (`201`). Used by the Part 1 UI.

## GET `/v1/ops/summary`

Aggregate counts for the dashboard (documents, decisions by disposition). Real DB aggregates — not frontend mocks.

## POST `/v1/query`

Grounded natural-language query over persisted verification data. Allow-listed intents only; **no LLM-generated SQL**. Unsupported / injection-like inputs return `UNSUPPORTED` (or equivalent safe refusal). See [query-interface.md](./query-interface.md).

## GET `/health` / `/ready` / `/metrics`

Liveness, database-schema/storage readiness, and Prometheus metrics. No auth.
