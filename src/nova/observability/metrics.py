"""Low-cardinality Prometheus metrics for the HTTP API."""

from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

HTTP_REQUESTS = Counter(
    "nova_http_requests_total",
    "Total HTTP requests.",
    labelnames=("method", "path", "status"),
)
HTTP_LATENCY = Histogram(
    "nova_http_request_latency_seconds",
    "HTTP request latency in seconds.",
    labelnames=("method", "path"),
)


def observe_http_request(*, method: str, path: str, status: int, duration_seconds: float) -> None:
    route = _normalize_path(path)
    HTTP_REQUESTS.labels(method=method, path=route, status=str(status)).inc()
    HTTP_LATENCY.labels(method=method, path=route).observe(duration_seconds)


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST


def _normalize_path(path: str) -> str:
    if path.startswith("/v1/documents/"):
        return "/v1/documents/{document_id}"
    if path.startswith("/v1/shipments/"):
        return "/v1/shipments/{shipment_id}"
    if path in {
        "/health",
        "/ready",
        "/metrics",
        "/v1/documents",
        "/v1/query",
        "/v1/ops/summary",
        "/v1/customers",
    }:
        return path
    return "unmatched"
