# Evaluation

Quality and accuracy evaluation for Nova’s extraction, validation, and decisioning.

## Purpose

Evaluation measures how well the pipeline performs on curated document sets. It complements—but does not replace—automated unit and integration tests.

## Current status

No evaluation harness or gold dataset exists yet. Define metrics and datasets here when available. Do not invent scores or claim unmeasured quality.

## Planned contents

| Topic | Status |
|-------|--------|
| Metrics (field-level, document-level, decision agreement) | Planned |
| Gold / labeled datasets policy | Planned |
| Regression evaluation process | Planned |
| Human review agreement studies | Planned |

## Principles

- Separate **evaluation** (quality) from **tests** (correctness of code contracts).
- Use anonymized or synthetic documents only.
- Report methodology and limitations with every result.
- Never fabricate evaluation outcomes.

## Related

- [Testing](../testing/)
- [Agents](../agents/)
- [Audits](../audits/)
