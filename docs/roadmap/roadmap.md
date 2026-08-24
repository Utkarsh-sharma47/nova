# Roadmap

## Phase 1 — Engineering foundation (current)

Requirements, product definition, architecture principles, documentation system, git workflow, CI foundation, AI governance, security baseline.

**Exit criteria:** Docs + CI scripts green; no application code required.

## Phase 2 — Stack selection & contracts

- Choose language/runtime, API framework, DB, LLM provider (ADRs)
- Define typed contracts for extraction, validation, routing
- Skeleton repo layout without full business logic
- Enable language-appropriate lint/type CI

## Phase 3 — Ingestion & Extractor Agent

- Document input path
- Extractor Agent with confidence + evidence
- Failure isolation, timeouts, retries
- Observability for extraction runs

## Phase 4 — Validation & Router

- Customer rules format + deterministic checks
- MATCH / MISMATCH / UNCERTAIN
- Router policies for AUTO_APPROVE / HUMAN_REVIEW / AMENDMENT_REQUEST
- Golden fixture tests; fail-safe defaults

## Phase 5 — Persistence, samples, evaluation harness

- Persist shipment/document/validation/decision
- Clean + messy samples
- Eval harness and recorded results
- Idempotency for re-processing

## Phase 6 — Query & UI

- Query API
- Grounded NL query layer
- Minimal B2B operations UI with evidence display

## Phase 7 — Hardening & Part 1 submission

- Demo runbook
- Failure-path demonstration
- Deploy simplicity pass
- Submission package completeness

## Part 2 — Forward (after Part 1)

- Email / file triggers
- Multiple attachments per shipment
- Cross-document validation
- Draft replies
- Human approval
- Outbound sending workflows

Part 2 must reuse Part 1 extension points (`docs/architecture/part2-extension-points.md`).
