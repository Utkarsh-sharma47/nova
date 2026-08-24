# Evaluation

Quality and accuracy evaluation for Nova’s extraction, validation, and decisioning.

## Documents
| Document | Status |
|----------|--------|
| [philosophy.md](./philosophy.md) | Done (Phase 1) |
| [agent-evaluation.md](./agent-evaluation.md) | Done (spec only — no harness) |
| [validator-evaluation.md](./validator-evaluation.md) | Done — Validator harness + measured reports |
| [evaluation-framework.md](./evaluation-framework.md) | Done — process and agent dimensions |
| [datasets.md](./datasets.md) | Done — Part 1 categories + Part 2 future |
| [metrics.md](./metrics.md) | Done — definitions; thresholds as calibration targets |
| [regression-policy.md](./regression-policy.md) | Done — mandatory fixed-dataset eval on prompt/model changes |
## Current status

Validator evaluation harness and synthetic fixtures are implemented. Run `python scripts/run_validator_eval.py` and read `docs/evaluation/reports/`. Do not invent scores; re-measure after behavioral changes.
Extractor/Router evaluation harnesses remain Phase later.
## Planned contents
| Topic | Status |
|-------|--------|
| Metrics (field-level, document-level, decision agreement) | Spec’d; harness later |
| Gold / labeled datasets (clean + messy samples) | Phase 5 |
| Regression evaluation process | Spec’d; automation Phase 5–7 |
| False AUTO_APPROVE safety bar | Spec’d as primary gate |
## Principles
- Separate **evaluation** (quality) from **tests** (correctness of code contracts).
- Use anonymized or synthetic documents only.
- Report methodology and limitations with every result.
- Never fabricate evaluation outcomes.
- Prompt/model changes are behavioral changes — see [trust-model](../agents/trust-model.md) and [regression-policy](./regression-policy.md).
## Related
- [Testing](../testing/)
- [Agents](../agents/)
- [Audits](../audits/)
- [ADR-0010](../decisions/0010-ai-agent-contracts-and-trust-model.md)
- Requirements `REQ-EXT-005`, `REQ-SUBMISSION-002`
| Doc | Purpose |
|-----|---------|
| [philosophy.md](./philosophy.md) | Goals / safety bar |
| [architecture.md](./architecture.md) | Harness shape |
| [evaluation-framework.md](./evaluation-framework.md) | Framework |
| [metrics.md](./metrics.md) | Metrics |
| [datasets.md](./datasets.md) | Datasets |
| [regression-policy.md](./regression-policy.md) | Regression |
| [agent-evaluation.md](./agent-evaluation.md) | Agent eval |
