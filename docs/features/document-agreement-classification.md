# Feature: Document confidence / agreement classification

## Summary

Part 1 adds a **deterministic analytical layer** that classifies each processed document
into `STRONG_AGREEMENT`, `PARTIAL_AGREEMENT`, or `WEAK_AGREEMENT` from existing
extraction confidence and validation outcomes.

This classification is **orthogonal** to Router `DecisionKind`
(`AUTO_APPROVE` / `HUMAN_REVIEW` / `AMENDMENT_REQUEST`). The Router remains the
authority for business disposition.

## Three distinct metrics

These are deliberately separate and are all reported:

| Metric | Question it answers | Field |
|--------|--------------------|-------|
| Field extraction confidence | Did the extractor read this value correctly? | `extraction.fields[].confidence` |
| Validation result | Does the value match the customer's expected rule? | `MATCH` / `MISMATCH` / `UNCERTAIN` |
| Document agreement | Does the whole document agree with customer expectations? | `document_confidence`, `agreement` |

A document can be read with 98% extraction confidence and still disagree
completely. Example: expected Incoterms `FOB`, document says `CIF` — extraction
confidence is high, validation is `MISMATCH`, and document agreement is low.
`document_confidence` therefore is **not** an extraction average;
`extraction_confidence` is reported alongside it for that purpose.

## Rules (deterministic)

**Extraction confidence** = average of **available** required-field extraction
confidence scores (never invents values). Missing required fields are omitted from
the average and block `STRONG_AGREEMENT`.

**Document agreement score** (`document_confidence`) = mean over **all** required
fields of `field_extraction_confidence × outcome_factor`:

| Field state | Factor | Rationale |
|-------------|--------|-----------|
| Validation `MATCH` | 1.00 | Read correctly and agrees |
| Validation `UNCERTAIN` | 0.50 | Never counted as a match |
| Validation `MISMATCH` | 0.00 | Disagreement contributes no agreement |
| No check ran for the field | 0.50 | Unvalidated is not a pass |
| Presence `AMBIGUOUS` | 0.25 | Conflicting evidence reduces reliability |
| Presence `MISSING` / `UNKNOWN` | 0.00 (contributes nothing) | Absent evidence is never a pass |

The denominator is always the full required-field count, so a document cannot
score highly by validating only a few fields. Each additional mismatch therefore
materially lowers the score, and a document with obvious validation failures can
never present as strongly reliable even when extraction was confident.

The agreement score is analytical only. It is **never** an input to the Router:
`AUTO_APPROVE` still requires the existing fail-closed safety conditions, and
`false_auto_approve_rate` remains 0.

Field-level confidence is produced by the extractor from the quality of the matched
evidence, never from a constant or a floor. For the heuristic MockLLM the signals are:
how specific the matched label was, whether the value parses as the field's declared
type, and whether the value carries ambiguity markers (`?`, `~`, "maybe"), OCR noise,
or embedded instruction text. Fields with conflicting candidates become `AMBIGUOUS`
with `CONFLICTING_EVIDENCE`; `MISSING`/`UNKNOWN` fields carry `confidence = null`.

| Category | Conditions |
|----------|------------|
| `STRONG_AGREEMENT` | Validation completed; all required fields `MATCH`; no `UNCERTAIN`/`MISMATCH`; complete required extraction; extraction confidence ≥ 0.85 **and** agreement score ≥ 0.85 |
| `PARTIAL_AGREEMENT` | Some `MATCH` plus attention needed (e.g. `UNCERTAIN`, or medium confidence) without `MISMATCH` / low-confidence / missing validation |
| `WEAK_AGREEMENT` | Any `MISMATCH`, low/missing extraction confidence, failed/missing validation, or insufficient evidence |

## Surfaces

- `GET /v1/ops/summary` — `agreement_outcomes` counts + agreement fields on `recent_documents`
- `GET /v1/documents` — optional `agreement=` filter; each item includes agreement + confidence
- `GET /v1/documents/{id}` — `agreement`, `document_confidence`,
  `document_confidence_percent`, `extraction_confidence`,
  `extraction_confidence_percent`, `agreement_reasons`
- Dashboard / document detail UI — agreement tag + agreement confidence %, with
  extraction confidence shown separately, both distinct from the decision
- Query intents: see [query-intelligence-api.md](query-intelligence-api.md)

No DB migration: derived at read time from persisted extraction + validation rows.

## Observed fixture behaviour

Real values from the demo fixtures (mock LLM provider):

| Fixture | Extraction | Agreement score | Agreement | Validation | Decision |
|---------|-----------|-----------------|-----------|------------|----------|
| `synthetic_invoice_clean.txt` | 93% | 93% | `STRONG_AGREEMENT` | `MATCH` | `AUTO_APPROVE` |
| `synthetic_invoice_rejected.txt` | 93% | 15% | `WEAK_AGREEMENT` | `MISMATCH` | `AMENDMENT_REQUEST` |
| `synthetic_invoice_messy.txt` | 38% | 4% | `WEAK_AGREEMENT` | `MISMATCH` | `HUMAN_REVIEW` |

The clean and rejected fixtures have identical extraction confidence and very
different agreement scores, which is the property this feature guarantees.

## Related

- `src/nova/domain/agreement.py`
- `src/nova/application/agreement_projection.py`
- [operations-ui.md](operations-ui.md)
- [query-intelligence-api.md](query-intelligence-api.md)
