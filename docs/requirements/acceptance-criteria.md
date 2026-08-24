# Part 1 acceptance criteria (consolidated)

Derived from `inventory.md`. A Part 1 delivery is acceptable when all **P0 Part 1** items below are demonstrably met.

## Product

- [ ] Nova is presented and demoed as an **operational trade-document verification system** (REQ-PROD-001, REQ-PROD-002).
- [ ] Blind auto-approval is prevented by policy; human review paths exist (REQ-PROD-003, REQ-PROD-004).

## Pipeline behavior

- [ ] Document input accepted into the pipeline (REQ-EXT-001).
- [ ] Required fields extracted with **confidence** and **evidence** (REQ-EXT-002–004).
- [ ] Customer-specific rules applied (REQ-VAL-001).
- [ ] Outcomes include **MATCH**, **MISMATCH**, and **UNCERTAIN** (REQ-VAL-002–004).
- [ ] Router emits **AUTO_APPROVE**, **HUMAN_REVIEW**, and **AMENDMENT_REQUEST** under documented policy (REQ-ROUTER-001–003).
- [ ] Failures do not silently auto-approve (REQ-ROUTER-005, REQ-EXT-006).

## Data & query & UI

- [ ] Shipment/document/validation/decision persisted (REQ-DATA-001).
- [ ] Query layer over persisted data, including NL query that does not invent facts (REQ-QUERY-001–003).
- [ ] Minimal B2B operations UI shows extraction, validation, and decision with evidence (REQ-UI-001–002).

## Quality & delivery

- [ ] Clean and messy samples evaluated; results recorded (REQ-EXT-005, REQ-SUBMISSION-001–002).
- [ ] Non-happy-path failure handling demonstrated (REQ-SUBMISSION-003).
- [ ] Observability: structured logs and run correlation (REQ-OBS-001–002, REQ-OBS-004).
- [ ] Technical documentation complete for implemented behavior (REQ-DOC-001).
- [ ] Secrets hygiene maintained (REQ-SEC-001–002).

## Explicitly not required for Part 1 acceptance

Email ingestion, multi-attachment workflows, cross-document validation, draft replies, human approval actions, outbound sending (see REQ-PART2-*). Extension points must exist in design, not full features.
