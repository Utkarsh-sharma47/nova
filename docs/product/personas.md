# Personas

Personas are derived from the assignment’s operational context (shipper ↔ validation team). No personas are invented beyond roles needed to operate Part 1 and extend Part 2.

## Primary

### Validation analyst

| Attribute | Detail |
|-----------|--------|
| Goal | Clear the review queue accurately and quickly |
| Jobs | Inspect evidence, confirm mismatches, escalate amendments |
| Pain today | Manual extraction, inconsistent rules, email threads |
| Nova use | HUMAN_REVIEW queue, field/evidence detail, decision rationale |

### Operations lead

| Attribute | Detail |
|-----------|--------|
| Goal | Predictable throughput with controlled risk |
| Jobs | Monitor volumes, auto-approve rates, amendment rates, failure spikes |
| Pain today | Weak metrics; surprises from missed mismatches |
| Nova use | Query persisted outcomes; observe run health |

## Secondary

### Rules owner / account ops

| Attribute | Detail |
|-----------|--------|
| Goal | Customer-specific rules applied as agreed |
| Jobs | Maintain rule packs per customer |
| Nova use | Validation against configured rules (Part 1); rule governance later as needed |

### Implementing engineer / evaluator

| Attribute | Detail |
|-----------|--------|
| Goal | Reliable, testable, observable pipeline |
| Jobs | Contracts, evals, traces, failure modes |
| Nova use | Fixtures, eval harness, observability |

### Assignment evaluator / reviewer

| Attribute | Detail |
|-----------|--------|
| Goal | Reproduce Part 1 claims from the repository |
| Jobs | Run samples, read docs, verify traceability |
| Nova use | Demo runbook, eval artifacts, requirements matrix |

## Indirect (Part 2+)

### Shipper contact

Receives amendment requests / draft communications after human approval gates. **Not a Part 1 UI user.**

## Persona → requirement links

| Persona | Key REQ IDs |
|---------|-------------|
| Validation analyst | REQ-UI-001–003, REQ-EXT-003–004, REQ-ROUTER-002 |
| Operations lead | REQ-QUERY-001–002, REQ-OBS-* |
| Rules owner | REQ-VAL-001 |
| Engineer / evaluator | REQ-TEST-*, REQ-SUBMISSION-*, REQ-AI-* |
| Shipper (Part 2) | REQ-PART2-005–007 |
