# ADR-0010: AI agent contracts and trust model

| Field | Value |
|-------|-------|
| Status | Accepted |
| Date | 2026-08-25 |
| Deciders | AI Systems Architect (Nova) |
| Supersedes | — |
| Superseded by | — |

## Context

Nova’s Part 1 pipeline depends on three conceptual agents—Extractor, Validator, and Router—before any LLM provider or orchestration stack is chosen. Without frozen contracts, later implementation risks:

- Silent fabrication of missing document fields
- LLM judgment overriding crisp rule comparisons
- Uncertainty collapsing into `MATCH` or `AUTO_APPROVE`
- Unversioned prompt edits treated as cosmetic rather than behavioral changes
- Evaluation that cannot regress safety properties

Requirements intent (assignment + engineering) calls for confidence, evidence, MATCH/MISMATCH/UNCERTAIN, AUTO_APPROVE/HUMAN_REVIEW/AMENDMENT_REQUEST, timeouts/retries, and auditable decisions.

## Decision

1. **Define typed contracts now** for Extraction, Validation, and Routing in [`docs/agents/contracts.md`](../agents/contracts.md), without implementing LLM calls, provider prompts, or agent runtimes.
2. **Field presence** must distinguish `KNOWN`, `UNKNOWN`, `MISSING`, and `AMBIGUOUS`; non-`KNOWN` fields require `value = null`.
3. **Validator** supports `MATCH` / `MISMATCH` / `UNCERTAIN`, with normative deterministic behavior for obvious comparisons; LLMs cannot override deterministic results for the same rule.
4. **Router** decisions are `AUTO_APPROVE` / `HUMAN_REVIEW` / `AMENDMENT_REQUEST`, subject to non-bypassable safety constraints; uncertainty and failures never silently become `AUTO_APPROVE`.
5. Adopt the **AI trust model** in [`docs/agents/trust-model.md`](../agents/trust-model.md): schema validation, evidence, confidence, bounded retries, model/prompt metadata, and prompt governance (version + eval gate).
6. Specify **evaluation/test classes** in [`docs/evaluation/agent-evaluation.md`](../evaluation/agent-evaluation.md) without building the harness yet.

## Alternatives considered

| Option | Pros | Cons |
|--------|------|------|
| Defer contracts until coding | Faster short-term | Freezes accidental shapes; hard to eval safely |
| Single “document agent” monolith | Fewer moving parts | Weak audit boundaries; harder fail-safe policy |
| Prompt-only routing without deterministic constraints | Flexible | Unsafe; opaque; fails assignment/engineering bars |
| Implement providers now with ad-hoc JSON | Demo sooner | Couples trust model to one stack; skips governance |

## Consequences

### Positive

- Implementation phases have a stable I/O and safety target.
- Prompt/model changes have an explicit governance path.
- False auto-approval can be tested as a contract/policy property.

### Negative / trade-offs

- Some fields (rules DSL, schema IDL, exact timeouts) remain configurable later.
- Stricter presence semantics may increase `HUMAN_REVIEW` rates (accepted trade for safety).

### Follow-up work

- Choose schema IDL and generate artifacts from these semantics.
- Implement agents against contracts with real eval fixtures.
- Customer policy threshold ADRs as needed.

## Compliance

Contributors and coding agents must:

- Keep stage boundaries and enum sets unless a new ADR supersedes this one.
- Update agent docs + evaluation docs when contracts or trust rules change.
- Never ship prompt/model changes as “docs-only” if behavior changes—run/record eval when harness exists.
- Refuse implementations that invent `KNOWN` values or auto-approve under uncertainty.

## References

- [`docs/agents/contracts.md`](../agents/contracts.md)
- [`docs/agents/extractor.md`](../agents/extractor.md)
- [`docs/agents/validator.md`](../agents/validator.md)
- [`docs/agents/router.md`](../agents/router.md)
- [`docs/agents/trust-model.md`](../agents/trust-model.md)
- [`docs/evaluation/agent-evaluation.md`](../evaluation/agent-evaluation.md)
- [`AGENTS.md`](../../AGENTS.md)
- [`ARCHITECTURE.md`](../../ARCHITECTURE.md)
