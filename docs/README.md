# Nova documentation

Authoritative detailed documentation for Nova. Root-level markdown files are overviews; this tree holds working specs, decisions, and templates.

## Who this is for

| Audience | Primary paths |
|----------|---------------|
| Developers | `architecture/`, `features/`, `api/`, `database/` |
| Reviewers / evaluators | `requirements/`, `evaluation/`, `roadmap/` |
| AI coding agents | Root `AGENTS.md`, `ai-development/`, then relevant feature/architecture docs |
| Operators | `operations/`, `observability/`, `deployment/` |
| Security | `security/` |

## Sections

| Directory | Contents |
|-----------|----------|
| [requirements/](requirements/) | REQ inventory, acceptance, traceability, scope |
| [product/](product/) | Problem, solution, personas |
| [architecture/](architecture/) | Principles, overview, Part 2 extension points, standards |
| [agents/](agents/) | Pipeline agent contracts |
| [features/](features/) | Feature docs (see template) |
| [api/](api/) | HTTP surface (design) |
| [database/](database/) | Domain model, ER, indexes, audit |
| [documents/](documents/) | Document processing (Phase 3) |
| [testing/](testing/) | Test strategy |
| [evaluation/](evaluation/) | Quality evaluation |
| [observability/](observability/) | Logs, metrics, traces |
| [deployment/](deployment/) | Deploy and CI/CD |
| [security/](security/) | Security baseline |
| [operations/](operations/) | Git workflow and runbooks |
| [decisions/](decisions/) | ADRs 0001–0010 |
| [ai-development/](ai-development/) | AI coding-agent governance |
| [audits/](audits/) | Audits |
| [roadmap/](roadmap/) | Phase detail |

## Templates

- [Feature template](features/FEATURE_TEMPLATE.md)
- [Agent template](agents/AGENT_TEMPLATE.md)
- [ADR template](decisions/ADR_TEMPLATE.md)
- [Audit template](audits/AUDIT_TEMPLATE.md)

## Writing rules

1. Be precise and useful. Do not invent undecided technologies or APIs.
2. Prefer linking `REQ-*` IDs and ADRs over restating contested decisions.
3. Update docs in the same change that alters behavior.
4. Reserved folders may keep a short README until implementation phases fill them.
