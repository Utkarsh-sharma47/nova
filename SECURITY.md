# Security

Security posture and expectations for Nova.

## Sensitivity

Nova processes trade shipping documents that may contain commercially sensitive data and personal information. Treat all document contents and derived fields as sensitive by default.

## Current status (Phase 11)

Production hardening for Part 1 Compose:

- Env-only secrets; **no secrets in images** (web auth via runtime `__NOVA_RUNTIME__`)
- Non-root API and nginx-unprivileged web containers
- CORS allow-list with production rejection of wildcards
- Upload + request body size limits and MIME allow-list (**implemented**)
- Structured JSON logs with secret redaction; safe error envelopes
- CI secret scan + dependency audits (`pip-audit`, `npm audit`)

**Remote production deploy: NOT EXECUTED.** See [`docs/deployment/production.md`](docs/deployment/production.md) and [`docs/audits/phase-11-production-readiness.md`](docs/audits/phase-11-production-readiness.md).

## Principles

- **Least privilege** for services, humans, and agents accessing documents.
- **No secrets in git.** Credentials and API keys belong in a secure secret store; never commit them.
- **Minimize retention** of raw documents and PII; define retention when storage is designed.
- **Audit decisions.** Prefer designs that can explain why a document was approved, reviewed, or rejected.
- **Safe defaults.** Prefer human review over auto-approve when confidence or policy is unclear.
- **Dependency discipline.** Do not add unnecessary dependencies; review new ones for supply-chain risk.
- **Validate LLM output** against Pydantic contracts before downstream use.

## Reporting issues

Until a formal vulnerability disclosure process exists, report suspected security issues privately to the repository maintainers. Do not open public issues that include exploit details or sample production data.

## Baseline + architecture

- [`docs/security/baseline.md`](docs/security/baseline.md) — repo hygiene + upload controls
- [`docs/security/architecture.md`](docs/security/architecture.md) — auth, CORS, containers, limits, LLM
- [`docs/security/query-api.md`](docs/security/query-api.md) — grounded query controls

## Related documents

- [docs/security/](docs/security/)
- [docs/operations/](docs/operations/)
- [AGENTS.md](AGENTS.md)
