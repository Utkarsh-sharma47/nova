# Phase 5 audit — Validator Agent

| Field | Value |
|-------|-------|
| Date | 2026-08-25 |
| Auditor | Principal Engineer |
| Scope | Validator Agent implementation, LLM boundary, safety failure modes, persistence, evaluation |
| Branch | `feature/phase-5-validator` |
| Related phase | Phase 5 (assignment naming); roadmap “Validation” capability |

## Verdict

**PASS** — no unresolved CRITICAL or HIGH findings after audit fixes.

Architecture flow holds:

`ExtractionResult` fields → deterministic validation → uncertainty handling → optional LLM judgment → `ValidationResult` → append-only persistence.

Validator does **not** perform routing decisions (`AUTO_APPROVE` / `HUMAN_REVIEW` / `AMENDMENT_REQUEST` absent from outputs).

## Method

Inspected:

- `src/nova/agents/validator/` (agent + deterministic engine)
- `src/nova/llm/` (`LLMPort`, `MockLLM`)
- `src/nova/validation_store/` (append-only)
- `src/nova/contracts/validation.py`
- `src/nova/evaluation/validator/` + `fixtures/evaluation/validator/`
- `tests/agents/validator/`, `tests/evaluation/validator/`, `tests/failure/validator/`

Ran:

- `ruff check src tests` — pass
- `mypy` — pass (65 source files)
- `pytest -q` — **66 passed, 2 skipped**
- Eval suite (`cases`) — n=16, unsafe_match=0, false_match_rate=0.0
- Regression suite — n=15, unsafe_match=0, blocking=False

Artifacts: `docs/evaluation/results/phase-5-validator-eval.json`, `phase-5-validator-regression.json`.

## Architecture checklist

| Criterion | Status |
|-----------|--------|
| Deterministic rules first | Done |
| Uncertainty → UNCERTAIN (not silent MATCH) | Done |
| Optional LLM judgment only when `requires_judgment` | Done |
| Typed `ValidationResult` | Done |
| Append-only persistence / idempotent store API | Done (in-memory + SQL models/migration on branch) |
| No routing decisions in Validator | Confirmed |

## Safety audit (attempted breaks)

| Attack / failure | Result |
|------------------|--------|
| LLM says MATCH when deterministic says MISMATCH | Deterministic MISMATCH locked; override blocked |
| LLM invents / hallucinated validation without evidence | UNCERTAIN (`MISSING_EVIDENCE` / blocked MATCH) |
| Missing evidence (`source_type=NONE`) | UNCERTAIN, not MATCH |
| Conflicting evidence | UNCERTAIN |
| Malformed LLM response | UNCERTAIN after bounded retries |
| LLM timeout | UNCERTAIN |
| Provider failure | UNCERTAIN |
| Unknown validation / rule op | UNCERTAIN (`UNKNOWN_RULE_OP`) |
| Database / store failure | Stage `FAILED` + `DATABASE_FAILURE`; not converted to MATCH |

## Findings

| ID | Severity | Finding | Status |
|----|----------|---------|--------|
| P5-001 | Critical | Validator Agent missing at audit start | **Resolved** — implemented |
| P5-002 | High | Evidence `NONE` could still MATCH | **Resolved** — requires non-NONE evidence |
| P5-003 | Med | Eval accuracy < 1.0 on a few non-safety disagreements | Accepted — unsafe_match=0 |
| P5-004 | Low | Dual package naming (`nova.agents.validator` vs `nova.validator`) | Accepted — agents package is runtime SoT |

## Contract compliance

- Outcomes: `MATCH` / `MISMATCH` / `UNCERTAIN`
- Stage status: `COMPLETED` / `FAILED`
- Deterministic flag + reasons/codes on checks
- Model metadata recorded when LLM used
- Extraction mutation avoided (deep copies)

## Observability / traceability

- Structured `validator_completed` logs with counts/status/error_code (no document snippets)
- `run_id` / `trace_id` propagated on contracts
- Eval fixtures + scored reports for regression gate

## Limitations (not blocking PASS)

- Router not implemented (Phase 6) — intentional
- Live LLM vendor adapter not enabled; CI uses `MockLLM`
- Full SQLAlchemy write path for validation rows may still be wired primarily via in-memory store in unit/eval; migration `validation_runs` present where merged
- Cross-document validation reserved (Part 2)

## Phase 6 readiness

Ready to consume `ValidationResult` for Router dispositions. Do not allow Router to treat Validator `FAILED` or blocking `UNCERTAIN`/`MISMATCH` as `AUTO_APPROVE`.

## Follow-ups

| Action | Owner |
|--------|-------|
| Wire orchestrator: Extractor → Validator → Router | Phase 6 |
| Promote SQL validation persistence in integration tests | Phase 5/6 |
| Calibrate remaining non-unsafe eval disagreements | Eval |

## Appendix — exact commands

```text
ruff check src tests          # All checks passed
mypy                          # Success: no issues found in 65 source files
pytest -q                     # 66 passed, 2 skipped
```
