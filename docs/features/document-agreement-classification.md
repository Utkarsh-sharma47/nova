# Feature: Document confidence / agreement classification

## Summary

Part 1 adds a **deterministic analytical layer** that classifies each processed document
into `STRONG_AGREEMENT`, `PARTIAL_AGREEMENT`, or `WEAK_AGREEMENT` from existing
extraction confidence and validation outcomes.

This classification is **orthogonal** to Router `DecisionKind`
(`AUTO_APPROVE` / `HUMAN_REVIEW` / `AMENDMENT_REQUEST`). The Router remains the
authority for business disposition.

## Rules (deterministic)

Document confidence = average of **available** required-field extraction confidence
scores (never invents values). Missing required fields are omitted from the average
and block `STRONG_AGREEMENT`. Heuristic MockLLM scores come from label specificity +
value clarity — not a constant `0.9`.

| Category | Conditions |
|----------|------------|
| `STRONG_AGREEMENT` | Validation completed; all required fields `MATCH`; no `UNCERTAIN`/`MISMATCH`; complete required extraction; avg confidence ≥ 0.85 |
| `PARTIAL_AGREEMENT` | Some `MATCH` plus attention needed (e.g. `UNCERTAIN`, or medium confidence) without `MISMATCH` / low-confidence / missing validation |
| `WEAK_AGREEMENT` | Any `MISMATCH`, low/missing extraction confidence, failed/missing validation, or insufficient evidence |

## Surfaces

- `GET /v1/ops/summary` — `agreement_outcomes` counts + agreement fields on `recent_documents`
- `GET /v1/documents` — optional `agreement=` filter; each item includes agreement + confidence
- `GET /v1/documents/{id}` — `agreement`, `document_confidence`, `document_confidence_percent`
- Dashboard / document detail UI — agreement tag + confidence %, separate from decision
- Query intents (allow-listed only):
  - `count_documents_by_agreement`
  - `list_documents_by_agreement`
  - `count_documents_requiring_attention`
  - `count_documents_by_decision`
  - `count_documents_with_mismatches`

No DB migration: derived at read time from persisted extraction + validation rows.

## Related

- `src/nova/domain/agreement.py`
- `src/nova/application/agreement_projection.py`
- [operations-ui.md](operations-ui.md)
- [query-intelligence-api.md](query-intelligence-api.md)
