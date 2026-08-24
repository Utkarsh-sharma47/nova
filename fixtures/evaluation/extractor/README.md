# Extractor evaluation fixtures

Synthetic-only golden/regression cases for the Extractor Agent.

**Never commit real customer or production shipping documents.**

## Layout

- `dataset.json` — pinned revision manifest (`extractor-regression-v1`)
- `cases/<id>/document.txt` — synthetic document text
- `cases/<id>/gold.json` — expected presence/values/status
- `cases/<id>/llm_response.json` (or `.txt`) — deterministic MockLLM script

## Regression rule

Any prompt, model, decoding, or Extractor agent behavior change requires re-running this fixed revision. Failures must be visible in the report — do not delete cases to silence regressions.
