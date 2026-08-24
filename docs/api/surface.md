# API surface

Conceptual HTTP API for Part 1. Detailed contracts: [contracts.md](./contracts.md). **Not implemented in Phase 2.**

Base path: `/api/v1`. Auth: API key/bearer on non-health routes (Part 1 assumption).

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/documents` | Ingest document |
| GET | `/documents/{document_id}` | Retrieve document |
| GET | `/shipments/{shipment_id}` | Retrieve shipment |
| GET | `/documents/{document_id}/validation` | Latest validation |
| GET | `/documents/{document_id}/decision` | Latest decision |
| POST | `/query` | Natural-language query |
| GET | `/health` | Liveness |
| GET | `/ready` | Readiness |

Per-endpoint notes: [endpoints.md](./endpoints.md).
