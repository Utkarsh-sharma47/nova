# Architecture principles

These principles constrain later implementation. Changing them requires an ADR.

1. **Operational system first** — Nova is a trade-document verification workflow with AI components, not a chatbot wrapped in CRUD.
2. **Typed contracts** — Stage inputs/outputs are schema-validated. Agents do not pass free-form blobs across trust boundaries without parsing.
3. **Deterministic validation where appropriate** — Crisp customer rules execute deterministically; LLMs assist judgment only when needed.
4. **LLMs for reasoning where appropriate** — Extraction, ambiguity handling, NL query interpretation may use LLMs; rule arithmetic should not.
5. **Confidence-aware AI** — Confidence is a first-class signal consumed by validation and routing.
6. **Evidence / grounding** — Extracted values carry evidence suitable for human audit.
7. **Human-in-the-loop** — HUMAN_REVIEW and amendment paths are core, not afterthoughts.
8. **Idempotency** — Re-processing the same document/run key must be safe.
9. **Observability** — Every run has correlation IDs and structured stage logs.
10. **Structured logging** — Machine-parseable logs; secrets and unnecessary PII redacted per policy.
11. **Failure isolation** — One stage failure does not corrupt unrelated runs; errors classify cleanly.
12. **Retry limits** — Retries are bounded; infinite retry loops are forbidden.
13. **Timeout handling** — LLM and I/O calls time out into safe failure paths.
14. **Cost controls** — Token/cost budgets and model choices are configurable and recorded.
15. **Auditability** — A reviewer can reconstruct why a decision was made.
16. **Reproducibility** — Model/prompt/version metadata retained for eval replay where practical.
17. **Testability** — Policies and deterministic logic are fixture-tested; evals cover LLM paths.
18. **Deployment simplicity** — Prefer a simple Part 1 deploy path over premature distributed complexity.
19. **Part 2 extensibility** — Ports/adapters for ingestion, multi-doc context, communications — without building Part 2 now.
20. **No silent architecture drift** — Contract or principle changes go through docs/ADR + PR.
