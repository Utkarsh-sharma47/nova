# API surface

Part 1 HTTP API. Detailed contracts: [contracts.md](./contracts.md).

Base path: `/v1`. Auth: API key/bearer on non-health routes.

| Method | Path | Purpose | Part 1 status |
|--------|------|---------|---------------|
| POST | `/v1/documents` | Ingest document (`Idempotency-Key`) | Implemented |
| GET | `/v1/documents` | List documents | Implemented |
| GET | `/v1/documents/{document_id}` | Retrieve document + extraction summary | Implemented |
| GET | `/v1/documents/{document_id}/validation` | Latest validation | Implemented |
| GET | `/v1/documents/{document_id}/decision` | Latest decision | Implemented |
| GET | `/v1/shipments/{shipment_id}` | Retrieve shipment | Implemented |
| GET | `/v1/shipments/{shipment_id}/validation` | Shipment validation alias | Implemented |
| GET | `/v1/shipments/{shipment_id}/decision` | Shipment decision alias | Implemented |
| POST | `/v1/customers` | Create customer (ops/demo) | Implemented |
| GET | `/v1/ops/summary` | Dashboard aggregates | Implemented |
| POST | `/v1/query` | Grounded NL query (no arbitrary SQL) | Implemented |
| GET | `/health` | Liveness | Implemented |
| GET | `/ready` | Readiness | Implemented |
| GET | `/metrics` | Prometheus metrics | Implemented |

Per-endpoint notes: [endpoints.md](./endpoints.md). Idempotency: [idempotency.md](./idempotency.md).
