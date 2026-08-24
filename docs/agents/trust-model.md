# AI trust model

How Nova treats LLMs as **probabilistic components** inside an operational verification system—not as authoritative decision-makers.

**Status:** Accepted design companion to [ADR-0002](../decisions/0002-ai-agent-contracts-and-trust-model.md)  
**Contracts:** [contracts.md](./contracts.md)

---

## Core premise

Large language models sample from distributions. Their outputs can be fluent, confident, and **wrong**. Nova therefore:

1. Constrains agents with **typed contracts**
2. Prefers **deterministic rules** wherever comparisons are crisp
3. Requires **evidence** and **confidence** for extracted claims
4. Routes uncertainty to **humans** or **amendments**, never to silent approval
5. Versions prompts and models as **behavioral changes** subject to evaluation

---

## Mandatory controls

| Control | Requirement |
|---------|-------------|
| Validate outputs | Every agent output is parsed and schema-validated before crossing a stage boundary |
| Enforce schemas | Unknown fields, wrong types, illegal enums are rejected or repaired under explicit `SCHEMA_REPAIR` uncertainty |
| Preserve evidence | Extracted values carry grounding; checks cite evidence or extraction evidence IDs |
| Track confidence | Confidence is first-class; low/missing confidence blocks `AUTO_APPROVE` when policy says so |
| Detect malformed output | Non-JSON / invariant violations are classified errors, not “best effort” accepts |
| Bound retries | Finite attempts; no infinite repair loops |
| Deterministic rules when possible | Equality, tolerances, allow-lists, presence rules run in deterministic code |
| Never silent approve on uncertainty | `UNCERTAIN`, `UNKNOWN`, `MISSING`, `AMBIGUOUS`, failures ≠ `AUTO_APPROVE` / false `MATCH` |
| Log model/version metadata | Persist `ModelInvocationMetadata` (model, prompt_version, config, timestamps, tokens/cost) |
| Support evaluation & regression | Prompt/model changes require eval against golden/adversarial sets before claiming improvement |

---

## Trust boundaries

```text
┌─────────────────────────────────────────────────────────┐
│  Untrusted: raw document bytes, model token streams     │
└──────────────────────────┬──────────────────────────────┘
                           │ schema parse + invariants
                           ▼
┌─────────────────────────────────────────────────────────┐
│  Trusted-enough stage objects: ExtractionResult,        │
│  ValidationResult, DecisionResult (contract-valid)      │
└──────────────────────────┬──────────────────────────────┘
                           │ deterministic safety constraints
                           ▼
┌─────────────────────────────────────────────────────────┐
│  Disposition: AUTO_APPROVE only if still eligible       │
└─────────────────────────────────────────────────────────┘
```

Free-form model prose never leaves a stage as the stage result. Optional `llm_rationale` on the Router is annotation only.

---

## Uncertainty is a first-class state

| Layer | Uncertainty representation |
|-------|----------------------------|
| Extraction | `FieldPresence`, `UncertaintyFlag`, confidence, warnings |
| Validation | `UNCERTAIN` check status |
| Routing | Disallow `AUTO_APPROVE`; prefer `HUMAN_REVIEW` / `AMENDMENT_REQUEST` |

Converting uncertainty into approval or `MATCH` without new evidence is a **trust-model violation**.

---

## Prompt governance

Prompts are behavioral artifacts equivalent to code. Treat changes like production logic changes.

### Version record (required for each production prompt revision)

| Field | Description |
|-------|-------------|
| `prompt_version` | Unique immutable id (e.g. `extractor.v3`, content-hash, or registry key) |
| `agent` | `extractor` \| `validator` \| `router` |
| `agent_version` | Agent package / module version bound to the prompt |
| `model` | Target model id(s) approved with this prompt |
| `temperature` / config | Generation parameters relevant to behavior |
| `timestamp` | When the version was published |
| `change_summary` | Why the prompt changed |
| `evaluation_result` | Reference to eval report (pass/fail + metrics artifact path or ID) |
| `approved_by` | Human approver for production promotion |

### Process

1. Draft prompt change on a branch (no silent prod edits).
2. Run contract/schema tests (must still pass).
3. Run agent evaluation suite (golden + adversarial + false `AUTO_APPROVE` bar).
4. Record `evaluation_result` on the version record.
5. Promote only if gates pass; persist `prompt_version` on every run’s `ModelInvocationMetadata`.

### Rules

- Prompt edits without eval are **not** production-ready.
- Changing model or temperature with the same prompt text is still a behavioral change → new eval.
- Do not claim quality improvements without recorded metrics.
- Rollback = pin previous `prompt_version` + `model` pair.

Concrete prompt registry storage is a later implementation concern; this section defines the governance contract.

---

## Cost and abuse bounds

- Per-run token/cost budgets (orchestrator-enforced when implemented).
- Timeouts on every model call ([agent docs](./README.md)).
- Retries bounded; exponential backoff recommended for transient errors.
- Document-derived prompt injection must not be able to emit illegal enums; post-validate always.

---

## Security constraints (AI-specific)

- No secrets in prompts, tools configs committed to git, or fixtures.
- Minimize PII in logged snippets; prefer locators over long verbatim text in logs.
- Validate tool/model arguments; do not execute open-ended tool loops.
- See also root `SECURITY.md` and `docs/security/` when present.

---

## What this phase does *not* include

- Live LLM provider integration
- Prompt text checked into a runtime registry
- Evaluation harness implementation
- Threshold numbers for specific customers

Those come in later phases against these contracts.

---

## Related documents

- [contracts.md](./contracts.md)
- [extractor.md](./extractor.md) · [validator.md](./validator.md) · [router.md](./router.md)
- [../evaluation/agent-evaluation.md](../evaluation/agent-evaluation.md)
- [`AGENTS.md`](../../AGENTS.md) runtime agent rules
