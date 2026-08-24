# Observability

Logging, metrics, and tracing for Nova.

## Purpose

Operators and developers must reconstruct why a document received a given decision. Observability design should support auditability without leaking sensitive document content into unsafe sinks.

## Current status

No observability stack has been chosen. Record tooling decisions as ADRs.

## Planned contents

| Topic | Status |
|-------|--------|
| Log fields and redaction rules | Planned |
| Core metrics (throughput, latency, decision mix) | Planned |
| Trace propagation across agents | Planned |
| Alerting policy | Planned |

## Guidance

- Prefer structured logs.
- Redact or hash sensitive fields by default.
- Tie decision IDs across extraction, rules, and review events.

## Related

- [Operations](../operations/)
- [Security](../security/)
- [Architecture](../architecture/)
