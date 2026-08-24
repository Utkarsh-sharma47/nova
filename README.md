# Nova

Nova is a multi-agent AI pipeline for trade shipping document validation.

It reads documents such as Bills of Lading and invoices, extracts key fields, checks them against customer rules, and decides whether to auto-approve, flag for human review, or request corrections. The goal is to replace manual email back-and-forth between shippers and validation teams.

## Status

Phase 1 — documentation foundation. Application implementation has not started.

## Documentation map

| Area | Path |
|------|------|
| Architecture overview | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Agent operating rules | [AGENTS.md](AGENTS.md) |
| Contributing | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Local development | [DEVELOPMENT.md](DEVELOPMENT.md) |
| Testing | [TESTING.md](TESTING.md) |
| Security | [SECURITY.md](SECURITY.md) |
| Roadmap | [ROADMAP.md](ROADMAP.md) |
| Changelog | [CHANGELOG.md](CHANGELOG.md) |
| Full docs tree | [docs/](docs/) |

### `docs/` sections

| Section | Purpose |
|---------|---------|
| [requirements/](docs/requirements/) | Problem statements, constraints, acceptance criteria |
| [product/](docs/product/) | Product goals, personas, workflows |
| [architecture/](docs/architecture/) | System design and boundaries |
| [agents/](docs/agents/) | Agent roles, contracts, and behavior |
| [features/](docs/features/) | Per-feature documentation |
| [api/](docs/api/) | External and internal interfaces |
| [database/](docs/database/) | Data model and persistence notes |
| [testing/](docs/testing/) | Test strategy and suites |
| [evaluation/](docs/evaluation/) | Quality and accuracy evaluation |
| [observability/](docs/observability/) | Logging, metrics, tracing |
| [deployment/](docs/deployment/) | Release and runtime deployment |
| [security/](docs/security/) | Threat model and controls |
| [operations/](docs/operations/) | Runbooks and operational practices |
| [decisions/](docs/decisions/) | Architecture Decision Records (ADRs) |
| [ai-development/](docs/ai-development/) | Guidance for AI-assisted development |
| [audits/](docs/audits/) | Periodic audits and findings |
| [roadmap/](docs/roadmap/) | Phased delivery plan |

## Quick start for contributors

1. Read [AGENTS.md](AGENTS.md) if you are an AI coding agent (or working with one).
2. Read [CONTRIBUTING.md](CONTRIBUTING.md) and [DEVELOPMENT.md](DEVELOPMENT.md).
3. Work on a feature branch; never push directly to `main`.
4. Update documentation when behavior or architecture changes.

## License

License not yet chosen.
