# Agent: Validator

| Field | Value |
|-------|-------|
| Status | Implemented (Phase 5) |
| Owner | Validation / AI Systems |
| Last updated | 2026-08-25 |
| Related ADR(s) | [ADR-0010](../decisions/0010-ai-agent-contracts-and-trust-model.md), [ADR-0005](../decisions/0005-ai-provider-abstraction.md) |
| Contract | [contracts.md](./contracts.md#validator-contract) |
| Implementation | `src/nova/agents/validator/` |
| Audit | [phase-5-audit.md](../audits/phase-5-audit.md) |

## Purpose

Compare extracted fields to customer-specific rules and emit auditable `MATCH` / `MISMATCH` / `UNCERTAIN` checks. Deterministic evaluation is default; LLM judgment is optional and cannot override crisp mismatches or invent evidence.

## Non-responsibilities

- Extraction (Extractor)
- Routing dispositions (Router) — Validator never emits `AUTO_APPROVE` / `HUMAN_REVIEW` / `AMENDMENT_REQUEST`

## Runtime notes

- Entry point: `ValidatorAgent.validate(ValidationRequest) -> ValidationResult`
- Persistence: append-only `validation_store` (tests/eval); SQL tables when migrations applied
- Default LLM: `MockLLM` via `LLMPort`

## Testing

- `tests/agents/validator/` — unit + safety invariants
- `tests/evaluation/validator/` — eval harness
- `tests/failure/validator/` — provider/malformed failures
- Fixtures: `fixtures/evaluation/validator/`

## Change history

| Date | Change |
|------|--------|
| 2026-08-25 | Contract defined |
| 2026-08-25 | Runtime Validator + Phase 5 audit PASS |
