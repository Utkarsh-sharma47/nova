# Feature: Router / Decision Agent (Phase 6)

| Field | Value |
|-------|-------|
| Status | Implemented |
| Owner | Decision and Routing Engineer |
| Last updated | 2026-08-25 |
| Related ADR(s) | [ADR-0010](../decisions/0010-ai-agent-contracts-and-trust-model.md) |
| Contract | [docs/agents/contracts.md](../agents/contracts.md), [docs/agents/router.md](../agents/router.md) |
| Package | `nova.router` |

## Summary

The Router consumes `ExtractionResult` + `ValidationResult` and emits a single
`DecisionResult` disposition:

- `AUTO_APPROVE`
- `HUMAN_REVIEW`
- `AMENDMENT_REQUEST`

Routing is **policy-first**. Deterministic safety constraints always outrank any
LLM suggestion. LLM output cannot authorize `AUTO_APPROVE`.

## Safety invariants

`AUTO_APPROVE` is impossible when any of the following hold:

- required / critical information is missing (`MISSING` / `UNKNOWN` / `AMBIGUOUS`)
- validation is `UNCERTAIN` (blocking) or `MISMATCH` (blocking)
- evidence is insufficient for known fields
- confidence is below policy high threshold
- Extractor or Validator stage failed
- LLM assist failed / malformed / suggested unsafe `AUTO_APPROVE`
- system failsafe or timeout path

`actor_type = system_failsafe` **cannot** store `AUTO_APPROVE` (Pydantic contract
+ application boundary + DB `CHECK`).

## Persistence

Append-only `decisions` table (migration `0002_phase6_decisions`) with:

- disposition, reason codes, evidence refs, confidence
- routing rule / agent versions, model metadata hooks
- `run_id` / `trace_id`, timestamp, input fingerprint
- unique one decision per `verification_run_id`

## Idempotency

Identical immutable inputs share an `input_fingerprint`. Repeated evaluation of
the same fingerprint returns a consistent disposition without inventing
contradictory approvals (no distributed lock).

## Out of scope

Frontend, Part 2 human-review UI, email workflows, external shipment systems.

## Tests

`tests/agents/router/test_router_decisions.py` covers AUTO_APPROVE eligibility,
missing information, MISMATCH, UNCERTAIN, low confidence, missing evidence,
extractor/validator/LLM failure, unsafe LLM override, system failsafe,
persistence boundary, and repeated evaluation.
