# Part 1 requirements

Authoritative list of requirements that Part 1 must satisfy. Part 2 items are excluded; see [part-2-forward-compatibility.md](./part-2-forward-compatibility.md).

Full cards live in [functional-requirements.md](./functional-requirements.md) and [non-functional-requirements.md](./non-functional-requirements.md).

## Part 1 pipeline obligations

| Stage | Must deliver | Primary REQ IDs |
|-------|--------------|-----------------|
| Input | Accept document into a verification run | REQ-EXT-001 |
| Extraction | Required fields + confidence + evidence | REQ-EXT-002–004, REQ-AI-001, REQ-AI-004 |
| Samples | Clean + messy fixtures for eval | REQ-EXT-005 |
| Validation | Customer rules → MATCH / MISMATCH / UNCERTAIN | REQ-VAL-001–004, REQ-AI-002 |
| Routing | AUTO_APPROVE / HUMAN_REVIEW / AMENDMENT_REQUEST | REQ-ROUTER-001–003, REQ-AI-003 |
| Persistence | Shipment, document, validation, decision | REQ-DATA-001 |
| Query | Programmatic + natural-language over stored data | REQ-QUERY-001–002 |
| UI | Minimal B2B operations surface | REQ-UI-001–002 |
| Evaluation / demo | Reproducible results + failure path | REQ-SUBMISSION-001–003 |
| Observability | Logs, run correlation, visible failures | REQ-OBS-001–002, REQ-OBS-004 |
| Documentation | Technical docs for what ships | REQ-DOC-001, REQ-DOC-004 |

## Part 1 inventory (ASSIGNMENT)

| ID | Priority | Description (short) | Status |
|----|----------|---------------------|--------|
| REQ-PROD-001 | P0 | Operational verification product framing | documented |
| REQ-PROD-002 | P0 | Replace manual email verification loop | documented |
| REQ-PROD-003 | P0 | No blind auto-approve under risk | documented |
| REQ-PROD-004 | P0 | Human review remains available | documented |
| REQ-EXT-001 | P0 | Document input | planned |
| REQ-EXT-002 | P0 | Extract required fields | planned |
| REQ-EXT-003 | P0 | Confidence per field | planned |
| REQ-EXT-004 | P0 | Evidence per field | planned |
| REQ-EXT-005 | P0 | Clean + messy samples | planned |
| REQ-VAL-001 | P0 | Customer-specific rules | planned |
| REQ-VAL-002 | P0 | MATCH | planned |
| REQ-VAL-003 | P0 | MISMATCH | planned |
| REQ-VAL-004 | P0 | UNCERTAIN | planned |
| REQ-ROUTER-001 | P0 | AUTO_APPROVE | planned |
| REQ-ROUTER-002 | P0 | HUMAN_REVIEW | planned |
| REQ-ROUTER-003 | P0 | AMENDMENT_REQUEST | planned |
| REQ-DATA-001 | P0 | Persist core records | planned |
| REQ-QUERY-001 | P0 | Query layer | planned |
| REQ-QUERY-002 | P0 | Natural-language query | planned |
| REQ-UI-001 | P0 | Minimal B2B UI | planned |
| REQ-AI-001 | P0 | Extractor Agent | planned |
| REQ-AI-002 | P0 | Validation stage | planned |
| REQ-AI-003 | P0 | Router Agent | planned |
| REQ-OBS-002 | P0 | End-to-end run tracing | planned |
| REQ-OBS-004 | P0 | Visible failure modes | planned |
| REQ-DOC-001 | P0 | Technical documentation | documented |
| REQ-DOC-004 | P1 | Demo/submission runbook | planned |
| REQ-SUBMISSION-001 | P0 | E2E Part 1 demonstration | planned |
| REQ-SUBMISSION-002 | P0 | Recorded reproducible eval | planned |
| REQ-SUBMISSION-003 | P0 | Failure-path demonstration | planned |

## Part 1 inventory (ENGINEERING — required to deliver safely)

| ID | Priority | Description (short) | Status |
|----|----------|---------------------|--------|
| REQ-EXT-006 | P0 | Isolated extraction failures | planned |
| REQ-VAL-005 | P0 | Deterministic validation where appropriate | planned |
| REQ-VAL-006 | P0 | Auditable validation records | planned |
| REQ-ROUTER-004 | P0 | Explicit routing policy | planned |
| REQ-ROUTER-005 | P0 | Fail-safe routing on errors | planned |
| REQ-DATA-002 | P0 | 1:N documents schema readiness | planned |
| REQ-DATA-003 | P1 | Idempotent re-processing | planned |
| REQ-DATA-004 | P1 | Retention / PII policy documented | planned |
| REQ-QUERY-003 | P0 | NL query must not invent facts | planned |
| REQ-UI-002 | P0 | Surface confidence/evidence in UI | planned |
| REQ-UI-003 | P1 | Readable HUMAN_REVIEW queue | planned |
| REQ-AI-004 | P0 | Confidence-aware; no silent hallucinations | planned |
| REQ-AI-005 | P0 | Timeouts, retries, cost controls | planned |
| REQ-AI-006 | P1 | Model/prompt version metadata | planned |
| REQ-OBS-001 | P0 | Structured logging | planned |
| REQ-OBS-003 | P1 | Token/cost metrics | planned |
| REQ-TEST-001 | P0 | Real deterministic tests | planned |
| REQ-TEST-002 | P0 | Golden validation/routing tests | planned |
| REQ-TEST-003 | P0 | No fake success-only tests | documented |
| REQ-TEST-004 | P0 | Agent I/O contract tests | planned |
| REQ-DEPLOY-001 | P0 | Honest CI foundation | planned |
| REQ-DEPLOY-002 | P0 | No premature/fake CI tools | planned |
| REQ-DEPLOY-003 | P1 | Simple demo deploy path | planned |
| REQ-DEPLOY-004 | P1 | Progressive CI completeness | planned |
| REQ-DOC-002 | P0 | AI agent governance | planned |
| REQ-DOC-003 | P0 | ADRs for major decisions | planned |
| REQ-SEC-001 | P0 | `.env` hygiene | planned |
| REQ-SEC-002 | P0 | No secrets in repo | planned |
| REQ-SEC-003 | P0 | Safe logging policy | planned |
| REQ-SEC-004 | P1 | Upload security (when upload exists) | deferred |
| REQ-SEC-005 | P1 | Dependency pinning strategy | planned |

## Part 1 definition of done

Part 1 is done when:

1. Every **ASSIGNMENT** P0 row above is `done` with evidence in the traceability matrix.
2. Every **ENGINEERING** P0 row above is `done` or explicitly waived by ADR with residual risk noted.
3. [acceptance-criteria.md](./acceptance-criteria.md) checklist is complete.
4. No Part 2 feature is required for the demo; extension points are documented.
