# Metrics

## Library choice

**`prometheus_client`** — small, widely used Python library that exposes a Prometheus text exposition format on `GET /metrics`. Chosen over a full APM/OTel stack for Part 1 ops foundation: low complexity, easy scrape, no mandatory sidecar.

## Baseline series

| Metric | Type | Labels | Purpose |
|--------|------|--------|---------|
| `nova_http_requests_total` | Counter | method, path, status | Request volume |
| `nova_http_request_latency_seconds` | Histogram | method, path | Latency |
| `nova_http_errors_total` | Counter | method, path, status | 5xx responses |
| `nova_document_ingestion_total` | Counter | status | Ingestion count (wired when ingestion lands) |
| `nova_document_processing_total` | Counter | stage, status | Processing attempts |
| `nova_document_processing_failures_total` | Counter | stage, error_code | Processing failures |

Path labels are normalized (`/health`, `/ready`, `/metrics`, `/api/*`) to avoid cardinality blow-ups.

## Non-goals (Part 1)

- No Grafana/Prometheus server bundled in Compose
- No distributed trace export required (trace IDs in logs are enough for Part 1)

ADR: [0007](../decisions/0007-observability.md).
