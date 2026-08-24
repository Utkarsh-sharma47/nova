# Scope boundaries

## In scope — Part 1 (implementation in later phases; specified now)

- Single-document verification path for trade/shipping docs (invoice, Bill of Lading, etc.)
- Extraction with confidence + evidence
- Customer-specific validation rules
- MATCH / MISMATCH / UNCERTAIN
- Router: AUTO_APPROVE / HUMAN_REVIEW / AMENDMENT_REQUEST
- Persistence of shipment/document/validation/decision
- Natural-language query over persisted data
- Minimal B2B operations UI
- Clean + messy samples and evaluation
- Observability, failure handling, technical documentation
- Demo/submission readiness

## In scope — Phase 1 only (this delivery)

- Requirements, product, architecture principles, standards
- Documentation system
- Git workflow
- CI foundation applicable to a docs-only repository
- AI development governance
- Security baseline for the repository
- Part 2 extension-point documentation (no Part 2 features)

## Out of scope for Phase 1

- Application code, agent implementations, database, UI
- LLM provider integration
- Real document processing pipeline
- Fake application unit tests
- Application-specific lint/type/build tooling before stack selection

## Out of scope for Part 1 (deferred to Part 2)

- Email/file triggers as primary ingestion
- Multiple attachments end-to-end workflows
- Cross-document consistency validation
- Draft replies
- Human approval actions / sending workflows

## Non-goals (general)

- Replacing human judgment for all edge cases
- Fully autonomous commercial settlement without review policies
- Building a general-purpose document AI platform unrelated to trade verification
- Over-engineered multi-region infra for the assignment demo

## Change control

Scope changes require:

1. Inventory update (`REQ-*` add/deprecate)
2. Roadmap note
3. ADR if architectural
4. PR description linking the REQ IDs
