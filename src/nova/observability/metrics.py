"""Baseline Prometheus metrics for Nova API.

Library choice: `prometheus_client` — small, standard for Python HTTP services,
exposes a scrapeable `/metrics` endpoint without a full observability platform.
"""

from __future__ import annotations

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)

REGISTRY = CollectorRegistry()

HTTP_REQUESTS = Counter(
    "nova_http_requests_total",
    "Total HTTP requests",
    labelnames=("method", "path", "status"),
    registry=REGISTRY,
)

HTTP_ERRORS = Counter(
    "nova_http_errors_total",
    "HTTP responses with status >= 500",
    labelnames=("method", "path", "status"),
    registry=REGISTRY,
)

HTTP_LATENCY = Histogram(
    "nova_http_request_latency_seconds",
    "HTTP request latency in seconds",
    labelnames=("method", "path"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=REGISTRY,
)

DOCUMENT_INGESTION = Counter(
    "nova_document_ingestion_total",
    "Documents accepted for ingestion (stub until ingestion is implemented)",
    labelnames=("status",),
    registry=REGISTRY,
)

DOCUMENT_PROCESSING = Counter(
    "nova_document_processing_total",
    "Document processing attempts (stub until pipeline is implemented)",
    labelnames=("stage", "status"),
    registry=REGISTRY,
)

DOCUMENT_PROCESSING_FAILURES = Counter(
    "nova_document_processing_failures_total",
    "Document processing failures (stub until pipeline is implemented)",
    labelnames=("stage", "error_code"),
    registry=REGISTRY,
)


def observe_http_request(*, method: str, path: str, status: int, duration_seconds: float) -> None:
    route = _normalize_path(path)
    status_label = str(status)
    HTTP_REQUESTS.labels(method=method, path=route, status=status_label).inc()
    HTTP_LATENCY.labels(method=method, path=route).observe(duration_seconds)
    if status >= 500:
        HTTP_ERRORS.labels(method=method, path=route, status=status_label).inc()


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST


def _normalize_path(path: str) -> str:
    """Collapse high-cardinality path segments for metric labels."""
    if path.startswith("/metrics"):
        return "/metrics"
    if path.startswith("/health"):
        return "/health"
    if path.startswith("/ready"):
        return "/ready"
    if path.startswith("/api/"):
        return "/api/*"
    return path.split("?")[0] or "/"
