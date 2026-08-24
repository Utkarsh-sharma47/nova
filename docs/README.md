# Documentation

Authoritative detailed documentation for Nova. Root-level markdown files are overviews; this tree holds working specs, decisions, and templates.

## Sections

| Directory | Contents |
|-----------|----------|
| [requirements/](requirements/) | Problem, constraints, acceptance criteria |
| [product/](product/) | Goals, personas, workflows |
| [architecture/](architecture/) | System design |
| [agents/](agents/) | Pipeline agents |
| [features/](features/) | Feature docs (see template) |
| [api/](api/) | Interfaces |
| [database/](database/) | Domain model, PostgreSQL schema, audit, DB test plan |
| [testing/](testing/) | Test strategy detail |
| [evaluation/](evaluation/) | Quality evaluation |
| [observability/](observability/) | Logs, metrics, traces |
| [deployment/](deployment/) | Deploy and runtime |
| [security/](security/) | Security detail |
| [operations/](operations/) | Runbooks |
| [decisions/](decisions/) | ADRs |
| [ai-development/](ai-development/) | AI-assisted development |
| [audits/](audits/) | Audits |
| [roadmap/](roadmap/) | Phase detail |

## Templates

- [Feature template](features/FEATURE_TEMPLATE.md)
- [Agent template](agents/AGENT_TEMPLATE.md)
- [ADR template](decisions/ADR_TEMPLATE.md)
- [Audit template](audits/AUDIT_TEMPLATE.md)

## Writing rules

- Be precise and useful.
- Do not invent undecided technologies or APIs.
- Prefer linking to ADRs over restating contested decisions.
- Update docs in the same change that alters behavior.
