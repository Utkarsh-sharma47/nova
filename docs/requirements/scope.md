# Scope

## In scope — Part 1 (specified now; implemented in later phases)

- Single-document verification path for trade/shipping documents (invoice, Bill of Lading, and other types only if introduced by samples/rules — not invented here)
- Document input into the pipeline
- Extraction of required fields with **confidence** and **evidence**
- Customer-specific validation rules
- Validation outcomes: **MATCH**, **MISMATCH**, **UNCERTAIN**
- Router dispositions: **AUTO_APPROVE**, **HUMAN_REVIEW**, **AMENDMENT_REQUEST**
- Persistence of shipment / document / validation / decision records
- Query layer over persisted data, including natural-language query
- Minimal B2B operations UI
- Clean sample + messy sample and evaluation
- Observability and failure handling
- Technical documentation
- Demo / submission readiness

## In scope — Phase 1 documentation delivery (this work)

- Assignment/product definition
- Functional and non-functional requirements with stable IDs
- Acceptance criteria and evaluation rubric
- Part 1 vs Part 2 separation
- Traceability matrix baseline

## Out of scope — Phase 1 documentation delivery

- Application code, agent implementations, database, frontend
- LLM provider integration
- Real document processing pipeline
- Fake application unit tests
- Application-specific lint/type/build tooling before stack selection

## Out of scope — Part 1 product (deferred to Part 2)

| Deferred capability | Forward-compat REQ |
|---------------------|--------------------|
| Email ingestion triggers | REQ-PART2-001 |
| File/attachment ingestion beyond Part 1 simple input (as primary multi-source workflow) | REQ-PART2-002 |
| Multiple documents per shipment end-to-end workflows | REQ-PART2-003 |
| Cross-document consistency validation | REQ-PART2-004 |
| Draft reply generation | REQ-PART2-005 |
| Human approval actions | REQ-PART2-006 |
| Outbound sending workflows | REQ-PART2-007 |

Part 1 **must not** hard-code designs that make these impossible; see [part-2-forward-compatibility.md](./part-2-forward-compatibility.md).

## Non-goals

- Replacing human judgment for all edge cases
- Fully autonomous commercial settlement without review policies
- Building a general-purpose document AI platform unrelated to trade verification
- Over-engineered multi-region infrastructure for the assignment demo
- Inventing features not present in the assignment (labeled engineering requirements only harden delivery)

## ASSIGNMENT vs ENGINEERING

| Type | Allowed |
|------|---------|
| **ASSIGNMENT REQUIREMENT** | Directly from assignment brief / project context |
| **ENGINEERING REQUIREMENT** | Safety, testability, observability, security, idempotency, fail-safe routing, typed contracts, Part 2 extension readiness |

Engineering requirements **do not** expand product scope (no new Part 1 features such as payment automation, carrier booking, or chat UX).

## Change control

Scope changes require:

1. Add/deprecate `REQ-*` with stable ID discipline
2. Update acceptance criteria and traceability matrix
3. ADR if architectural
4. PR description linking affected REQ IDs
