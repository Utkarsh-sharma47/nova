"""Synthetic decision evaluation fixtures.

Dataset ID: `nova-decision-eval`  
Revision: see `manifest.json`

## Contents

- `cases.jsonl` — labeled Router inputs (extraction + validation + optional LLM suggestion)
- `manifest.json` — revision, calibration target for false AUTO_APPROVE rate, versions

## Categories

Fifteen coverage categories plus a `critical_safety` slice that attempts unsafe
LLM `AUTO_APPROVE` paths. All critical cases must remain non-approve.

## Hygiene

Synthetic / anonymized only. No real customer PII or production documents.

## Regression

Cases tagged `regression` form the fixed routing regression set. Prompt, model,
or policy changes that affect Router behavior must re-run this suite
(see `docs/evaluation/regression-policy.md`).
"""
