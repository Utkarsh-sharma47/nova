# ADR-0007: Observability architecture

| Field | Value |
|-------|-------|
| Status | Accepted |
| Date | 2026-08-25 |
| Deciders | Principal Software Architect (Phase 2) |
| Supersedes | — |
| Superseded by | — |

## Context

### Problem

Verification decisions must be reconstructable across Extractor → Validator → Router.

### Requirements

- Structured logs with correlation / trace / request / agent execution IDs
- Metrics for latency, LLM failures, tokens/cost, validation/routing outcomes
- Health and readiness probes
- No secrets or unnecessary PII in logs

## Decision

1. **Structured logging** — JSON logs with fields in `docs/observability/architecture.md`.
2. **Metrics** — names frozen now; Prometheus or structured metric events in Phase 3+.
3. **Health** — `GET /health`, `GET /ready`.
4. **Tracing** — propagate `trace_id`; OpenTelemetry export optional for Part 1.

## Alternatives considered

| Option | Pros | Cons |
|--------|------|------|
| Print/debug only | Fast | Not auditable |
| Full OTel + Jaeger day one | Strong tracing | Ops heavy |
| Proprietary APM only | Nice UI | Lock-in |

## Consequences

### Advantages

Run reconstruction; cost visibility.

### Disadvantages

Discipline required to avoid PII leakage.

### Operational cost

Low if logs go to stdout.

### Complexity

Low–moderate.

### Developer velocity

Slight upfront cost for ID propagation helpers.

### Testing implications

Assert IDs on log/context in integration tests later.

### Deployment implications

Stdout collection; optional `/metrics`.

### Part 2 compatibility

Workers reuse same ID propagation.

### Migration risk

Low if attribute names stay stable.

## Compliance

- Every agent invocation gets `agent_execution_id`.
- LLM port records tokens/cost when available.
- Follow security redaction rules.

## References

- `REQ-OBS-001`–`004`
- [`docs/observability/architecture.md`](../observability/architecture.md)
