# Part 1 acceptance criteria (consolidated)

Derived from `inventory.md`. A Part 1 delivery is acceptable when all **P0 Part 1** items below are demonstrably met.

Authoritative evidence-driven statuses: [`../audits/final-part1-audit.md`](../audits/final-part1-audit.md).

## Product

- [x] Nova is presented and demoed as an **operational trade-document verification system** (REQ-PROD-001, REQ-PROD-002).
- [x] Blind auto-approval is prevented by policy; human review paths exist (REQ-PROD-003, REQ-PROD-004).

## Pipeline behavior

- [x] Document input accepted into the pipeline (REQ-EXT-001).
- [x] Required fields extracted with **confidence** and **evidence** (REQ-EXT-002–004).
- [x] Customer-specific rules applied (REQ-VAL-001).
- [x] Outcomes include **MATCH**, **MISMATCH**, and **UNCERTAIN** (REQ-VAL-002–004).
- [x] Router emits **AUTO_APPROVE**, **HUMAN_REVIEW**, and **AMENDMENT_REQUEST** under documented policy (REQ-ROUTER-001–003).
- [x] Failures do not silently auto-approve (REQ-ROUTER-005, REQ-EXT-006).

## Data & query & UI

- [x] Shipment/document/validation/decision persisted (REQ-DATA-001).
- [x] Query layer over persisted data, including NL query that does not invent facts (REQ-QUERY-001–003).
- [x] Minimal B2B operations UI shows extraction, validation, and decision with evidence (REQ-UI-001–002).

## Quality & delivery

- [x] Clean and messy samples evaluated; results recorded (REQ-EXT-005, REQ-SUBMISSION-001–002).
- [x] Non-happy-path failure handling demonstrated (REQ-SUBMISSION-003).
- [x] Observability: structured logs and run correlation (REQ-OBS-001–002, REQ-OBS-004).
- [x] Technical documentation complete for implemented behavior (REQ-DOC-001).
- [x] Secrets hygiene maintained (REQ-SEC-001–002).

## Explicitly not required for Part 1 acceptance

Email ingestion, multi-attachment workflows, cross-document validation, draft replies, human approval actions, outbound sending (see REQ-PART2-*). Extension points must exist in design, not full features.
