# Security

Security posture and expectations for Nova.

## Sensitivity

Nova processes trade shipping documents that may contain commercially sensitive data and personal information. Treat all document contents and derived fields as sensitive by default.

## Current status

Phase 2 security architecture is documented: [`docs/security/architecture.md`](docs/security/architecture.md). Runtime enforcement lands with implementation phases.

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

- [`docs/security/baseline.md`](docs/security/baseline.md) — repo hygiene
- [`docs/security/architecture.md`](docs/security/architecture.md) — auth, documents, injection, deps

## Related documents

- [docs/security/](docs/security/)
- [docs/operations/](docs/operations/)
- [AGENTS.md](AGENTS.md)
