# Performance testing

Defines what Nova measures for latency, throughput, and cost. **Does not implement** benchmark tooling or invent numeric SLOs.

Thresholds and budgets are **calibration targets** to be set from measured baselines on representative hardware and provider tiers.

---

## Goals

1. Make stage-level and end-to-end latency visible before production claims.
2. Separate **LLM latency** from application and database latency.
3. Track **cost per document** alongside quality (cheap + wrong is a failure).
4. Keep performance jobs honest: report methodology, concurrency, model versions, and fixture mix.

---

## Metrics

| Metric | Definition (intent) | Notes |
|--------|---------------------|-------|
| Document processing latency | Wall time from accepted submission to terminal decision (or terminal failure) | Primary user-facing latency |
| Stage latency — ingestion | Accept → content stored / run ready for extract | Include virus/type checks if present |
| Stage latency — extraction | Extractor start → structured result or error | Usually LLM-dominated |
| Stage latency — validation | Validator start → outcomes | Prefer deterministic path timing separately from any LLM-assist path |
| Stage latency — routing | Router start → disposition | Policy-only vs LLM-assist split when both exist |
| Stage latency — persistence | Write of core records | Include retry delays when measuring “durable” completion |
| LLM latency | Provider round-trip time(s) per run | Sum and max; record model ID |
| Database latency | Query/write timings for hot paths | p50/p95 when tooling exists |
| Throughput | Successfully completed documents per unit time at fixed concurrency | State fixture mix and failure rate |
| Cost per document | Estimated provider cost (tokens × price) + any billed OCR/storage extras attributed to the run | Use configured price tables; never invent production invoices |

Additional useful breakdowns (when instrumented): queue wait time, retry overhead, cold-start vs warm.

---

## Calibration targets (not final thresholds)

Until baselines exist, treat the following as **placeholders to calibrate**, not gates:

| Target class | How to establish | Used for |
|--------------|------------------|----------|
| p50 / p95 document latency | Measure on clean + messy fixture mixes under agreed concurrency | Ops dashboards; later SLOs |
| Max acceptable LLM share of E2E latency | Measure LLM vs non-LLM split | Optimization focus |
| Sustained throughput | Load suite on staging-like env | Capacity planning |
| Cost per document band | Eval + benchmark runs with pinned model/prompt versions | Budgeting; model choice |
| Failure overhead | Latency of timeout/retry paths | UX and timeout budget design |

**Do not** publish pass/fail numeric SLOs in CI until calibration is recorded in an ADR or ops doc with methodology.

---

## Benchmark scenarios (planned)

| Scenario | Fixture mix | Concurrency | Purpose |
|----------|-------------|-------------|---------|
| Smoke latency | 1 clean document | 1 | Sanity after deploys |
| Mixed quality | Clean + messy + missing-field | Low | Realistic latency |
| Provider stress | Repeated extract calls | Medium | LLM latency variance |
| Persistence stress | Many small writes/reads | Medium | DB latency |
| Cost snapshot | Fixed regression eval set | 1 | Cost per document trend |

Part 2 future scenarios (document only): multi-attachment shipments, email-ingestion lag — not Part 1 delivery.

---

## Isolation rules

1. Pin model ID, prompt version, and decoding settings in every report.
2. Separate cold-start runs from steady-state when relevant.
3. Do not mix evaluation quality scoring into performance pass/fail (report both; gate separately).
4. Never hide timeouts by infinite retry in benchmarks.

---

## CI placement

| Job | Role |
|-----|------|
| PR CI | No heavy benchmarks by default |
| Scheduled / manual benchmark | Trend latency, throughput, cost |
| Release | Compare to calibrated targets; explain regressions |

Performance regressions alone should not be “fixed” by deleting assertions or shortening timeouts unsafely.

---

## Relationship to evaluation

Evaluation reports may **include** latency and cost as secondary columns. Performance testing owns methodology for load and capacity; evaluation owns quality labels and safety metrics.

---

## Implementation status

Benchmark harness: **not implemented**. This document is the architecture only.

---

## Related

- [test-strategy.md](./test-strategy.md)
- [evaluation metrics](../evaluation/metrics.md)
- [observability philosophy](../observability/philosophy.md)
- Roadmap Phase 5–7 hardening
