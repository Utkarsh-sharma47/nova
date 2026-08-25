# Feature: Part 1 operations UI

## Summary

Phase 9 delivers a minimal React + TypeScript + Vite B2B operations UI for Nova Part 1.
Reviewers can upload a document, watch processing, inspect extraction/validation/decision,
browse shipments, and ask grounded questions through the Query API.

## Requirements

- `REQ-UI-001` — minimal B2B operations UI
- `REQ-UI-002` — surface confidence, evidence, validation outcomes
- `REQ-UI-003` — HUMAN_REVIEW queue readable in Part 1
- `REQ-QUERY-001`–`003` — consume document/shipment/validation/decision and grounded query APIs
- `REQ-OBS-004` — structured errors with `trace_id` visible for correlation

## Pages / routes

| Route | Purpose |
|-------|---------|
| `/` | Dashboard — ops summary totals, recent documents/decisions |
| `/upload` | Multipart upload with `Idempotency-Key` |
| `/documents/:documentId` | Metadata, extraction, validation, decision |
| `/shipments/:shipmentId` | Shipment identity and linked documents |
| `/query` | `POST /v1/query` with explicit supported-intent guidance |

## API integration

Typed client in `frontend/src/api/`:

- `POST /v1/customers` — create demo/ops customer
- `GET /v1/ops/summary?customer_id=` — dashboard aggregates (DB-backed)
- `GET /v1/documents?customer_id=` — recent documents
- `POST /v1/documents` — ingest
- `GET /v1/documents/{id}` (+ validation/decision)
- `GET /v1/shipments/{id}`
- `POST /v1/query`
- `GET /health`

All meaningful application data comes from these APIs. The UI does not invent aggregates.

## Status presentation

Badges cover lifecycle (`PROCESSING` / `PROCESSED` / `FAILED` mapped from wire statuses),
validation (`MATCH` / `MISMATCH` / `UNCERTAIN`), and decisions
(`AUTO_APPROVE` / `HUMAN_REVIEW` / `AMENDMENT_REQUEST`). Status is never color-only.

Dashboard metrics expose document pipeline totals, routing dispositions, and validation
aggregates from `GET /v1/ops/summary`. Recent document rows join in-decision dispositions
from the same summary payload when available (no invented decisions).

`AUTO_APPROVE` is displayed only when returned by the API.

Upload uses a step-style workflow (Customer → Shipment → Document → Upload → Result)
and explains acceptance as queued for processing. Query provides example allow-listed
questions; unsupported intents remain `UNSUPPORTED`.

## Error handling

Every fetch path exposes loading / success / empty / error, with a **Try again** action
when retry is appropriate. Structured API errors show `code`, `message`, `retryable`, and
`trace_id` in a technical section. Raw stack traces are never rendered. API string fields
are rendered as text (no `dangerouslySetInnerHTML`).

## Security

- API base URL and local demo token via `VITE_*` env vars (see `frontend/.env.example`)
- No production secrets committed
- Document field values treated as sensitive operational data in the UI

## Testing

Vitest + Testing Library under `frontend/src/**/*.test.tsx` with mocked fetch.
Coverage includes upload success/validation/409, document/validation/decision rendering,
HUMAN_REVIEW / AMENDMENT_REQUEST, query RESULT/EMPTY/UNSUPPORTED/FAILURE, network failure,
loading states, and XSS non-execution.

## Demo

[`../operations/ui-demo.md`](../operations/ui-demo.md) using `fixtures/demo/synthetic_invoice.txt`.

## Part 2 extension points

- Approval action pages / outbound reply drafts
- Role-aware HUMAN_REVIEW queues
- Multi-document shipment workspace
- Auth gateway replacing shared API key in the browser

## Related

- ADR-0009 frontend stack
- [`../architecture/frontend.md`](../architecture/frontend.md)
- [`../testing/frontend.md`](../testing/frontend.md)
- [`../deployment/frontend.md`](../deployment/frontend.md)
