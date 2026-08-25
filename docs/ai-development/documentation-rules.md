# Documentation rules for AI-assisted development

Every meaningful change must leave documentation accurate and discoverable.

## Documentation rule (mandatory)

Every meaningful feature must update, as applicable:

| Change type | Required documentation |
|-------------|------------------------|
| Feature / behavior | Feature documentation under `docs/features/` |
| External or internal API | API documentation under `docs/api/` |
| Testable behavior change | Testing documentation under `docs/testing/` (and tests themselves) |
| Architecture / boundaries / contracts | Architecture docs and/or ADR under `docs/decisions/` |
| AI behavior (prompts, routing policy, confidence thresholds, evaluation) | Evaluation docs under `docs/evaluation/` and agent docs under `docs/agents/` |

If a category does not apply, say so in the PR rather than skipping silently when it does apply.

## When documentation is required

Update docs when any of the following change:

- User-visible behavior
- Agent contracts, prompts, or decision policies
- Validation outcomes or router decision rules
- Data model / persistence semantics
- Configuration, env vars, or operational runbooks
- Security controls or threat assumptions
- Acceptance criteria or scope boundaries

## Quality bar

- Prefer precise, testable language over marketing language.
- Link related docs instead of duplicating long explanations.
- Record assumptions and open questions explicitly.
- Do not leave docs that contradict implemented behavior.
- Do not claim Phase 2 capabilities as delivered in Part 1.

## AI coding agent reporting

When finishing a task, the agent’s report should list:

- Docs files added or updated
- Docs intentionally unchanged (and why)
- Any documentation debt deferred (with owner/follow-up if known)

## Related documents

- [`architecture-rules.md`](./architecture-rules.md)
- [`agent-task-template.md`](./agent-task-template.md)
- [`review-checklist.md`](./review-checklist.md)
