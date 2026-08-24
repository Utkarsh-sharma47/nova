# Evaluation datasets

Categories and governance for Nova labeled evaluation data. No gold files are committed in this change.

**Hygiene:** synthetic or anonymized documents only. Never commit real customer PII or production shipping documents.

---

## Purpose

Datasets make Extractor, Validator, and Router quality **measurable and regressable**. Categories below define coverage; concrete fixtures arrive in implementation phases (clean + messy minimum: `REQ-EXT-005`).

---

## Part 1 categories

| Category | Description | Typical gold expectations |
|----------|-------------|---------------------------|
| **Clean documents** | Well-formed layout, readable text, complete required fields | High extraction agreement; stable validation; AUTO_APPROVE only if rules/policy truly satisfied |
| **Messy documents** | Poor layout, noise, stamps, skewed scans, mixed fonts | Calibrated confidence; UNCERTAIN and/or HUMAN_REVIEW rather than false certainty or false AUTO_APPROVE |
| **Missing fields** | Required business fields absent from the document | Missing-field detection; no invented values; MISMATCH or UNCERTAIN / AMENDMENT_REQUEST per rules |
| **Ambiguous fields** | Multiple plausible values, unclear labels, conflicting headers | UNCERTAIN preferred over forced MATCH; evidence should reflect ambiguity |
| **OCR corruption** | Garbled characters, broken tokens, line bleed | Lower confidence; extraction errors should not cascade into AUTO_APPROVE |
| **Conflicting documents** | Internal contradictions on a single document (or header vs body) | UNCERTAIN or MISMATCH with reasons; never silent resolve-to-approve |
| **Incorrect values** | Readable but wrong relative to customer rules / expected shipment facts | Validator MISMATCH; Router AMENDMENT_REQUEST or HUMAN_REVIEW per policy |
| **Unknown values** | Symbols, languages, or codes outside supported vocabulary | Explicit unknown/unsupported handling; no hallucination of canonical codes |
| **Adversarial inputs** | Prompt-injection-like text in document body, misleading “approve” instructions, spoofed stamps | System ignores instruction-like content for policy; no AUTO_APPROVE from adversarial text alone |

A single fixture may tag multiple categories (e.g. messy + missing fields).

---

## Minimum Part 1 coverage

Before claiming evaluation completeness for Part 1:

| Must have | Rationale |
|-----------|-----------|
| ≥1 clean labeled sample | Happy-path quality |
| ≥1 messy labeled sample | `REQ-EXT-005`; safety under noise |
| Explicit missing-field cases | Anti-hallucination |
| At least one case per validation outcome | MATCH, MISMATCH, UNCERTAIN gold |
| At least one case per router disposition | AUTO_APPROVE, HUMAN_REVIEW, AMENDMENT_REQUEST gold |
| ≥1 fail-safe / adversarial or hard-error adjacent case | False AUTO_APPROVE pressure |

Exact counts grow with calibration; do not invent a large synthetic farm without labeling budget.

---

## Part 2 future categories

Documented for extension planning only — **do not implement Part 2 product features in Part 1**.

| Category | Description |
|----------|-------------|
| **Multiple attachments** | Several files per shipment; ordering and type mix |
| **Cross-document conflicts** | Invoice vs Bill of Lading (etc.) disagree on shared fields |
| **Email content** | Body/thread context plus attachments; headers, signatures, quoted replies |

Evaluation harness design should allow multi-document contexts later without renaming MATCH/MISMATCH/UNCERTAIN.

---

## Label schema (intent)

Each labeled item should eventually record:

- Dataset ID + item ID + revision
- Document type and category tags
- Gold extracted fields (with normalized forms)
- Gold missing / unknown markers
- Gold validation outcomes per rule (or per field)
- Gold router disposition + rationale notes
- Labeler, date, known ambiguities
- License / synthetic provenance

Optional: evidence spans for audit of evidence-correctness metrics.

---

## Splits

| Split | Use |
|-------|-----|
| **Smoke** | Tiny set for manual/dev runs |
| **Regression (fixed)** | Pinned; required for prompt/model changes — see [regression-policy.md](./regression-policy.md) |
| **Calibration / holdout** | Used to set thresholds; not endlessly retuned against |
| **Exploratory** | New hard cases before promotion into regression |

Never silently move failing exploratory cases out of regression to “make green.”

---

## Versioning

- Dataset revisions are immutable once used in a published report.
- Adding items creates a new revision; reports cite the revision.
- Prompt/model experiments must declare which dataset revision they used.

---

## Storage (planned)

Fixtures and labels will live in a future controlled path (e.g. `fixtures/evaluation/` or equivalent) with README provenance. Paths are not fixed until implementation ADR.

---

## Related

- [evaluation-framework.md](./evaluation-framework.md)
- [metrics.md](./metrics.md)
- [regression-policy.md](./regression-policy.md)
- [failure testing](../testing/failure-testing.md) for infrastructure faults vs document difficulty
