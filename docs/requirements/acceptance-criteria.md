# Acceptance criteria

Consolidated Part 1 acceptance checklist derived from stable `REQ-*` IDs.

A Part 1 delivery is **acceptable** when every **P0 Part 1** item below is demonstrably met with evidence linked from the [traceability matrix](./traceability-matrix.md).

## Product

- [ ] Nova is presented and demoed as an **operational trade-document verification system** — REQ-PROD-001, REQ-PROD-002
- [ ] Blind auto-approval is prevented by policy; human review paths exist — REQ-PROD-003, REQ-PROD-004

## Pipeline behavior

- [ ] Document input accepted into the pipeline — REQ-EXT-001
- [ ] Required fields extracted with **confidence** and **evidence** — REQ-EXT-002, REQ-EXT-003, REQ-EXT-004
- [ ] Customer-specific rules applied — REQ-VAL-001
- [ ] Outcomes include **MATCH**, **MISMATCH**, and **UNCERTAIN** — REQ-VAL-002, REQ-VAL-003, REQ-VAL-004
- [ ] Router emits **AUTO_APPROVE**, **HUMAN_REVIEW**, and **AMENDMENT_REQUEST** under documented policy — REQ-ROUTER-001, REQ-ROUTER-002, REQ-ROUTER-003
- [ ] Failures do not silently auto-approve — REQ-ROUTER-005, REQ-EXT-006

## Data, query, and UI

- [ ] Shipment / document / validation / decision persisted — REQ-DATA-001
- [ ] Query layer over persisted data, including NL query that does not invent facts — REQ-QUERY-001, REQ-QUERY-002, REQ-QUERY-003
- [ ] Minimal B2B operations UI shows extraction, validation, and decision with evidence — REQ-UI-001, REQ-UI-002

## Quality and delivery

- [ ] Clean and messy samples evaluated; results recorded — REQ-EXT-005, REQ-SUBMISSION-001, REQ-SUBMISSION-002
- [ ] Non-happy-path failure handling demonstrated — REQ-SUBMISSION-003
- [ ] Observability: structured logs and run correlation — REQ-OBS-001, REQ-OBS-002, REQ-OBS-004
- [ ] Technical documentation complete for implemented behavior — REQ-DOC-001
- [ ] Secrets hygiene maintained — REQ-SEC-001, REQ-SEC-002

## Engineering P0 gates (must also pass)

- [ ] Deterministic vs LLM validation boundary documented and tested where applicable — REQ-VAL-005, REQ-VAL-006
- [ ] Routing policy explicit and fail-safe — REQ-ROUTER-004, REQ-ROUTER-005
- [ ] Distinct Extractor / Validator / Router contracts — REQ-AI-001, REQ-AI-002, REQ-AI-003, REQ-AI-004
- [ ] LLM timeouts/retries/cost controls — REQ-AI-005
- [ ] Real tests (no fake green) and contract/golden coverage — REQ-TEST-001, REQ-TEST-002, REQ-TEST-003, REQ-TEST-004
- [ ] CI applicable and honest — REQ-DEPLOY-001, REQ-DEPLOY-002

## Explicitly not required for Part 1 acceptance

These are **Part 2** capabilities. Part 1 must preserve extension points only (see REQ-PART2-*):

- Email ingestion as primary trigger
- Multi-attachment end-to-end workflows
- Cross-document consistency validation
- Draft reply generation
- Human approval *actions* and outbound sending workflows

## Auditor sign-off

| Check | Result | Reviewer | Date |
|-------|--------|----------|------|
| All P0 Part 1 acceptance items evidenced | ☐ | | |
| No invented features beyond assignment + labeled engineering requirements | ☐ | | |
| Part 2 remains unimplemented but extension-compatible | ☐ | | |
| Traceability matrix complete for assignment requirements | ☐ | | |
