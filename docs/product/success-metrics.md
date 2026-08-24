# Success metrics

Metrics measure whether Nova delivers the operational outcomes in [system-of-outcomes.md](./system-of-outcomes.md). Targets below are **evaluation guidance** for Part 1 delivery — not invented SLA products.

## Part 1 delivery metrics (assignment)

| Metric | Definition | Evidence | Related REQ |
|--------|------------|----------|-------------|
| Pipeline completeness | Clean sample runs extract → validate → route → persist | Demo + logs | REQ-SUBMISSION-001 |
| Outcome coverage | MATCH, MISMATCH, UNCERTAIN each produced in fixtures | Golden suite | REQ-VAL-002–004 |
| Router coverage | AUTO_APPROVE, HUMAN_REVIEW, AMENDMENT_REQUEST each produced | Golden suite | REQ-ROUTER-001–003 |
| Sample pair | Clean + messy samples evaluated | Eval artifacts | REQ-EXT-005 |
| Failure safety | At least one non-happy-path ends safely (no silent approve) | Demo notes | REQ-SUBMISSION-003, REQ-ROUTER-005 |
| Grounded query | NL answers cite records or refuse | Eval cases | REQ-QUERY-002–003 |
| Traceability | Every ASSIGNMENT Part 1 REQ has test + evidence | Matrix | traceability-matrix |

## Quality metrics (engineering)

| Metric | Definition | Notes |
|--------|------------|-------|
| Extraction field recall (clean) | Required fields present vs schema | Report per sample; no invented field list here |
| Low-confidence rate (messy) | Share of fields below policy threshold | Should rise on messy vs clean |
| False AUTO_APPROVE on failure | Count of fail→AUTO_APPROVE | Must be **0** in tests |
| Deterministic rule pass rate | Fixture rules evaluated without LLM | Unit suite |
| Eval reproducibility | Same command → same report inputs/outputs | Checked into or generated for submission |

## Operational metrics (once running)

Track after Part 1 implementation exists; not required as live production telemetry in Phase 1 docs:

| Metric | Intent |
|--------|--------|
| Auto-approve rate | Share of runs AUTO_APPROVE under policy |
| Human-review rate | Share routed to humans |
| Amendment-request rate | Share needing shipper correction |
| Median time-to-disposition | Ingestion → decision |
| Cost per run | Tokens/cost where LLM used (REQ-OBS-003) |

## Explicit non-metrics

Do not optimize for:

- Maximum auto-approve rate without safety gates
- “Agent count” or prompt length
- UI visual polish over evidence visibility
- Implementing Part 2 features to inflate demo scope

## Rubric link

Scoring weights and pass thresholds: [`../requirements/evaluation-rubric.md`](../requirements/evaluation-rubric.md).
