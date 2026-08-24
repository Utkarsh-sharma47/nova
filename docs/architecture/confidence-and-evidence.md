# Confidence and evidence model

Linked: `REQ-EXT-003`, `REQ-EXT-004`, `REQ-AI-004`, `REQ-ROUTER-005`, [ADR-0010](../decisions/0010-ai-agent-contracts-and-trust-model.md).

## Confidence

Each extracted field carries `confidence` in `[0.0, 1.0]` and `confidence_source` (`MODEL` | `HEURISTIC` | `HUMAN` | `UNKNOWN`).

### Bands

Labels over the continuous score. Numeric edges are **calibration parameters** in versioned policy — not magic prompt constants.

| Band | Initial interpretive range (provisional) | Typical use |
|------|------------------------------------------|-------------|
| `HIGH` | `>= high_threshold` (default **0.85**) | Eligible for AUTO_APPROVE if rules MATCH |
| `MEDIUM` | between thresholds | Usually HUMAN_REVIEW if blocking |
| `LOW` | `< low_threshold` (default **0.60**) | Elevated uncertainty |

Missing confidence ⇒ treat as **UNKNOWN** (not HIGH). Changing thresholds requires policy version bump + eval note.

## Evidence

`evidence_type`: `SNIPPET` | `PAGE_REGION` | `PAGE_REF` | `NONE`, plus optional snippet/page/bbox/processor_ref.

`NONE` + high confidence is a smell — policy may downgrade trust.

## Uncertainty codes

`NONE`, `MISSING`, `LOW_CONFIDENCE`, `AMBIGUOUS`, `CONTRADICTORY`, `UNSUPPORTED_DOC_TYPE`, `UNKNOWN`.

## Hard safety rule

```text
UNKNOWN or UNCERTAIN (blocking) ⇏ AUTO_APPROVE
```

Part 1 has **no** default policy upgrading UNKNOWN → AUTO_APPROVE.
