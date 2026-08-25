# Phase 6 audit — Router / Decision Agent

| Field | Value |
|-------|-------|
| Date | 2026-08-25 |
| Auditor | Principal Safety Engineer |
| Scope | Router / Decision Agent (assignment Phase 6) |
| Branch | `feature/phase-6-router` |
| Related docs | `docs/agents/router.md`, `docs/features/router-decision-agent.md`, ADR-0010 |
| Verdict | **PASS** (no unresolved CRITICAL or HIGH findings) |

## 1. Scope

Audited the complete Phase 6 Router implementation end-to-end:

- Typed contracts (`RoutingRequest` / `DecisionResult`)
- Deterministic safety constraints
- Optional advisory LLM assist
- System failsafe + DB constraint
- Decision persistence / idempotency
- Adversarial and evaluation suites
- Observability hooks

**Out of scope for this audit:** Extractor/Validator internal quality, frontend/UI, Part 2 human approval workflow, live provider credentials.

**Trust rule:** Prior reports were not trusted. Findings are based on inspecting source under `src/nova/router/`, contracts, migrations, tests, and commands re-run in this audit.

## 2. Architecture

Verified data flow:

```text
ExtractionResult
      +
ValidationResult
      ↓
RouterService.decide()   (deterministic constraints first)
      ↓
DecisionResult
      ↓
decisions (PostgreSQL) via DecisionRepository / DecisionRecord
```

| Check | Result |
|-------|--------|
| Router performs extraction | **No** — consumes `ExtractionResult` only |
| Router re-runs deterministic validation | **No** — consumes `ValidationResult` checks |
| LLM can authorize `AUTO_APPROVE` | **No** — sanitized / overridden; final gate present |
| Fail closed on agent/timeout/malformed | **Yes** — `actor_type=system_failsafe`, `HUMAN_REVIEW` |

Primary runtime: `src/nova/router/service.py`, `constraints.py`, `llm.py`, `persistence.py`.

## 3. Decision rules

| Condition | Observed disposition |
|-----------|----------------------|
| All blocking MATCH + critical fields KNOWN/high confidence/evidence | `AUTO_APPROVE` |
| Blocking `MISMATCH` | `AMENDMENT_REQUEST` (policy default) |
| Blocking `UNCERTAIN` / missing / unknown / ambiguous / low confidence | `HUMAN_REVIEW` |
| Extraction or validation `FAILED` | `HUMAN_REVIEW` |
| Timeout / force failsafe / engine error | `HUMAN_REVIEW` + `system_failsafe` |
| LLM suggests `AUTO_APPROVE` while blocked | Non-approve + `SC_UNSAFE_LLM_OVERRIDE` |

Policy snapshot versions (`policy_id` / `policy_version`) and `routing_rule_version` / `agent_version` are persisted on the decision.

## 4. Safety invariants

Hard constraints in `evaluate_safety_constraints` cover:

- validation failed / empty checks
- extraction failed / partial
- blocking MISMATCH / UNCERTAIN
- critical field MISSING / UNKNOWN / AMBIGUOUS
- low confidence / missing evidence
- contradictory validation summary vs checks
- policy deny-unknown (Part 1 default)

Contract-level invariant: `DecisionResult` rejects `system_failsafe` + `AUTO_APPROVE` and rejects `AUTO_APPROVE` with fired safety constraints.

## 5. AUTO_APPROVE adversarial audit

Attempted / covered paths (unit + evaluation). All must fail closed (not `AUTO_APPROVE`):

| Attack / fault | Result |
|----------------|--------|
| Missing fields | Fail closed |
| UNKNOWN / MISSING / AMBIGUOUS presence | Fail closed |
| UNCERTAIN validation | Fail closed |
| MISMATCH | Fail closed (`AMENDMENT_REQUEST`) |
| Missing evidence | Fail closed |
| Low confidence | Fail closed |
| Extractor failure | Fail closed |
| Validator failure | Fail closed |
| LLM failure / malformed output | Fail closed |
| LLM forces `AUTO_APPROVE` under mismatch/uncertainty | Overridden; `unsafe_llm_attempt=true` |
| Prompt injection correlation / rationale | Ignored for disposition |
| Contradictory validation inputs | Fail closed |
| System failsafe / timeout | `HUMAN_REVIEW` + failsafe actor |

**False `AUTO_APPROVE` count on labeled eval set: 0.**

## 6. Database / persistence

| Requirement | Evidence |
|-------------|----------|
| Decision history | Append-only `decisions` table; unique per `verification_run_id` |
| Auditability | `reason_codes`, `reasons`, `safety_constraints_applied`, `reasoning_json` |
| Reason codes | Persisted JSONB list |
| Run IDs | `verification_run_id` + `trace_id` |
| Version metadata | `policy_version`, `routing_rule_version`, `agent_version` |
| Failsafe constraint | `CHECK (actor_type <> 'system_failsafe' OR disposition <> 'AUTO_APPROVE')` |
| App boundary | `assert_failsafe_cannot_auto_approve` / `FailsafeAutoApproveError` |

Migration: `alembic/versions/0002_phase6_decisions.py`.

Confirmed: `system_failsafe` cannot persist `AUTO_APPROVE` (contract + app + SQLite CHECK test).

## 7. Testing (exact results)

Commands re-run on `feature/phase-6-router`:

```text
ruff check src tests     → All checks passed! (exit 0)
mypy                     → Success: no issues found in 58 source files (exit 0)
pytest -q                → 84 passed, 2 skipped (exit 0)
git diff --check         → clean (exit 0)
```

## 8. Evaluation

Harness: `nova.evaluation.decision.runner.run_decision_evaluation`

Dataset: `nova-decision-eval` revision `2026-08-25.r1` (22 outcomes including idempotent replay)

| Metric | Value |
|--------|-------|
| n | 22 |
| decision_accuracy | 1.0 |
| auto_approve_precision | 1.0 |
| false_auto_approve_count | 0 |
| false_auto_approve_rate | 0.0 |
| false_auto_approve_gate_passed | true |
| unsafe_decision_attempts | 7 (all correctly blocked) |
| failures | [] |

## 9. Observability

Router logs decision start/completion with `run_id`, `trace_id`, disposition, reason code, duration, actor type. Sensitive document contents are not logged. Prometheus decision counters are not yet first-class HTTP metrics (see findings).

## 10. Traceability

| Requirement | Coverage |
|-------------|----------|
| REQ-ROUTER-001 AUTO_APPROVE | Unit + eval golden |
| REQ-ROUTER-002 HUMAN_REVIEW | Unit + eval |
| REQ-ROUTER-003 AMENDMENT_REQUEST | Unit + eval |
| REQ-ROUTER-005 fail-safe | Failsafe/timeout/LLM failure tests |
| Trust model (no silent approve) | Constraints + adversarial eval |

## 11. Findings

| ID | Severity | Finding | Evidence | Recommendation | Status |
|----|----------|---------|----------|----------------|--------|
| P6-001 | CRITICAL | (none open) | — | — | — |
| P6-002 | HIGH | (none open) | — | — | — |
| P6-003 | MEDIUM | Router not yet wired into HTTP orchestration path | No `/v1/.../decide` route; decisions persisted via repository/helpers | Wire orchestrator after Extractor/Validator stages | Open (Phase 7+) |
| P6-004 | MEDIUM | Live LLM provider not integrated | `RouterLlmPort` / embedded suggestion only | Keep advisory; add provider behind port with eval gate | Open (by design) |
| P6-005 | LOW | Helper `validation_blocks_auto_approve` ignores `blocking=False` | `routing.py` helper | Align helper with constraint engine or deprecate | Open |
| P6-006 | LOW | Prometheus lacks dedicated decision counters | `observability/metrics.py` HTTP-only | Add `nova_router_decisions_total{decision=}` | Open |

## 12. Limitations

- No end-to-end API call that runs Extractor → Validator → Router in one request yet.
- Threshold calibration is policy-default (0.85); customer-specific policies not loaded from a store.
- Evaluation uses synthetic fixtures, not production documents.
- SQLite CHECK enforcement differs slightly from PostgreSQL; PostgreSQL remains the production target.

## 13. Phase 7 readiness

**Ready to proceed** for hardening / integration work, with these prerequisites:

1. Integrate Router into verification-run orchestration after Extractor + Validator.
2. Retain false `AUTO_APPROVE` gate at 0 on labeled fixtures as a release bar.
3. Address P6-003 before claiming pipeline completeness.
4. Do not treat LLM assist as authoritative in any future prompt change without re-running the decision eval suite.

## 14. Verdict

**PASS.** CRITICAL and HIGH findings: none unresolved. Safety bar for Phase 6 Router is met: unsafe paths fail closed; `system_failsafe` cannot persist `AUTO_APPROVE`; evaluation false `AUTO_APPROVE` rate is 0.
