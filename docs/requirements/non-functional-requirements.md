# Non-functional requirements

Quality, reliability, observability, security, testing, deployment, and documentation requirements. Same card schema as functional requirements.

## Legend

| Field | Allowed values |
|-------|----------------|
| **Source** | `ASSIGNMENT REQUIREMENT` · `ENGINEERING REQUIREMENT` |
| **Priority** | `P0` · `P1` · `P2` |
| **Scope** | `Part 1` · `Part 2` · `Both` |
| **Status** | `documented` · `planned` · `in_progress` · `done` · `deferred` |

---

## REQ-AI — LLM operations (NFR)

### REQ-AI-005

| Field | Value |
|-------|-------|
| **ID** | REQ-AI-005 |
| **Description** | LLM calls have timeouts, retry limits, and cost controls. |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Configurable limits exist; exhausted retries follow a safe failure path (no silent auto-approve). |
| **Implementation phase** | 3–4 |
| **Test strategy** | Unit/integration tests for timeout and retry budget |
| **Evidence** | Config docs; failure tests |
| **Status** | planned |

### REQ-AI-006

| Field | Value |
|-------|-------|
| **ID** | REQ-AI-006 |
| **Description** | Prompts, models, and versions are recorded for reproducibility of a verification run. |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P1 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Run metadata stores model/prompt version identifiers for LLM-backed stages. |
| **Implementation phase** | 3–5 |
| **Test strategy** | Integration assertion on metadata fields |
| **Evidence** | Trace/metadata samples |
| **Status** | planned |

---

## REQ-OBS — Observability

### REQ-OBS-001

| Field | Value |
|-------|-------|
| **ID** | REQ-OBS-001 |
| **Description** | Structured logging across pipeline stages. |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Logs are structured (for example JSON) and include correlation/run IDs. |
| **Implementation phase** | 3–5 |
| **Test strategy** | Integration checks on log shape |
| **Evidence** | Log samples |
| **Status** | planned |

### REQ-OBS-002

| Field | Value |
|-------|-------|
| **ID** | REQ-OBS-002 |
| **Description** | Trace each document through extraction → validation → routing → persistence. |
| **Source** | ASSIGNMENT REQUIREMENT (observability) / ENGINEERING REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | A single run ID ties stage events together for a verification. |
| **Implementation phase** | 3–5 |
| **Test strategy** | Integration trace demo |
| **Evidence** | Trace samples / observability docs |
| **Status** | planned |

### REQ-OBS-003

| Field | Value |
|-------|-------|
| **ID** | REQ-OBS-003 |
| **Description** | Record token/cost metrics per run where LLMs are used. |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P1 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Cost/token fields available for sample runs used in demos/evals. |
| **Implementation phase** | 3–5 |
| **Test strategy** | Integration sample |
| **Evidence** | Metrics sample |
| **Status** | planned |

### REQ-OBS-004

| Field | Value |
|-------|-------|
| **ID** | REQ-OBS-004 |
| **Description** | Failure modes are visible and classified (timeouts, parse errors, rule-engine errors). |
| **Source** | ASSIGNMENT REQUIREMENT (failure handling) / ENGINEERING REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Error taxonomy documented; failures queryable via logs/API fields. |
| **Implementation phase** | 4–5 |
| **Test strategy** | Failure tests |
| **Evidence** | Error taxonomy doc; failure fixtures |
| **Status** | planned |

---

## REQ-TEST — Testing

### REQ-TEST-001

| Field | Value |
|-------|-------|
| **ID** | REQ-TEST-001 |
| **Description** | Automated unit/integration tests cover non-LLM deterministic logic. |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | CI runs real tests; failing tests fail the build. |
| **Implementation phase** | 3+ |
| **Test strategy** | CI pipeline |
| **Evidence** | CI logs |
| **Status** | planned |

### REQ-TEST-002

| Field | Value |
|-------|-------|
| **ID** | REQ-TEST-002 |
| **Description** | Golden/fixture tests cover validation and routing policies. |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Fixture suite covers MATCH/MISMATCH/UNCERTAIN and all three router outcomes. |
| **Implementation phase** | 4–5 |
| **Test strategy** | CI golden suite |
| **Evidence** | Test report |
| **Status** | planned |

### REQ-TEST-003

| Field | Value |
|-------|-------|
| **ID** | REQ-TEST-003 |
| **Description** | No fake success-only application tests. |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Tests assert behavior; CI contains no placeholder always-green app tests. |
| **Implementation phase** | 1+ |
| **Test strategy** | CI/config review |
| **Evidence** | Workflow review notes |
| **Status** | documented |

### REQ-TEST-004

| Field | Value |
|-------|-------|
| **ID** | REQ-TEST-004 |
| **Description** | Contract tests validate agent I/O schemas. |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Invalid agent payloads are rejected by schema validation. |
| **Implementation phase** | 3–4 |
| **Test strategy** | Contract suite in CI |
| **Evidence** | Contract test report |
| **Status** | planned |

---

## REQ-DEPLOY — Deployment / CI

### REQ-DEPLOY-001

| Field | Value |
|-------|-------|
| **ID** | REQ-DEPLOY-001 |
| **Description** | CI foundation exists and fails correctly when checks fail. |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Applicable GitHub Actions (or equivalent) run; failures are non-green. |
| **Implementation phase** | 1 |
| **Test strategy** | CI self-check / deliberate failure review |
| **Evidence** | Workflow files + run history |
| **Status** | planned |

### REQ-DEPLOY-002

| Field | Value |
|-------|-------|
| **ID** | REQ-DEPLOY-002 |
| **Description** | Do not add application linters/typecheckers/build steps before the corresponding stack exists. |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | CI only runs checks applicable to current repository contents; gaps are documented rather than faked. |
| **Implementation phase** | 1 |
| **Test strategy** | CI config review |
| **Evidence** | Deployment/CI docs |
| **Status** | planned |

### REQ-DEPLOY-003

| Field | Value |
|-------|-------|
| **ID** | REQ-DEPLOY-003 |
| **Description** | Deployment remains simple for Part 1 demo (single environment acceptable). |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P1 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Deploy docs describe a minimal runnable path for reviewers. |
| **Implementation phase** | 7 |
| **Test strategy** | Smoke deploy/run |
| **Evidence** | Deploy documentation |
| **Status** | planned |

### REQ-DEPLOY-004

| Field | Value |
|-------|-------|
| **ID** | REQ-DEPLOY-004 |
| **Description** | Eventual CI enforces formatting/linting, static analysis, type checking, tests, build validation, and documentation consistency where practical. |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P1 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Roadmap tracks progressive CI enablement as the stack appears. |
| **Implementation phase** | 1→7 |
| **Test strategy** | CI growth review |
| **Evidence** | Roadmap + workflows |
| **Status** | planned |

---

## REQ-DOC — Documentation

### REQ-DOC-001

| Field | Value |
|-------|-------|
| **ID** | REQ-DOC-001 |
| **Description** | Technical documentation covers requirements, architecture, agents, and operations as they are established. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Requirements/product baseline exists; later phases add architecture/agents/ops as implemented. |
| **Implementation phase** | 1+ |
| **Test strategy** | Documentation structure review |
| **Evidence** | `docs/` tree |
| **Status** | documented |

### REQ-DOC-002

| Field | Value |
|-------|-------|
| **ID** | REQ-DOC-002 |
| **Description** | AI coding agents must follow repository governance (read rules before changing code; update docs when behavior changes). |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | `AGENTS.md` (or equivalent) exists when AI-assisted development is used; governance is documented. |
| **Implementation phase** | 1 |
| **Test strategy** | Doc review |
| **Evidence** | `AGENTS.md` / governance docs |
| **Status** | planned |

### REQ-DOC-003

| Field | Value |
|-------|-------|
| **ID** | REQ-DOC-003 |
| **Description** | Significant architectural decisions are captured as ADRs. |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Both |
| **Acceptance criteria** | ADRs exist for major choices; updates accompany architectural changes. |
| **Implementation phase** | 1+ |
| **Test strategy** | Doc review |
| **Evidence** | `docs/decisions/` (or equivalent) |
| **Status** | planned |

### REQ-DOC-004

| Field | Value |
|-------|-------|
| **ID** | REQ-DOC-004 |
| **Description** | Demo/submission instructions are documented when implementation exists. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P1 |
| **Scope** | Part 1 |
| **Acceptance criteria** | A runbook lists how to run samples and demonstrate Part 1. |
| **Implementation phase** | 7 |
| **Test strategy** | Manual following of runbook |
| **Evidence** | Ops/demo runbook |
| **Status** | planned |

---

## REQ-SEC — Security

### REQ-SEC-001

| Field | Value |
|-------|-------|
| **ID** | REQ-SEC-001 |
| **Description** | `.env` files are ignored; `.env.example` may exist without real secrets. |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | `.gitignore` excludes `.env`; example file has placeholders only. |
| **Implementation phase** | 1 |
| **Test strategy** | Secret-pattern / ignore check |
| **Evidence** | `.gitignore`, `.env.example` |
| **Status** | planned |

### REQ-SEC-002

| Field | Value |
|-------|-------|
| **ID** | REQ-SEC-002 |
| **Description** | No API keys or credentials in source, docs, or tests. |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Secret pattern scan is clean in CI or pre-commit checks. |
| **Implementation phase** | 1+ |
| **Test strategy** | Secret scan |
| **Evidence** | CI logs |
| **Status** | planned |

### REQ-SEC-003

| Field | Value |
|-------|-------|
| **ID** | REQ-SEC-003 |
| **Description** | Safe logging policy: no secrets; careful handling of document PII in logs. |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Policy documented; implementation complies when logging is added. |
| **Implementation phase** | 1 (policy) → 5 (code) |
| **Test strategy** | Policy review; log redaction tests later |
| **Evidence** | Security baseline docs |
| **Status** | planned |

### REQ-SEC-004

| Field | Value |
|-------|-------|
| **ID** | REQ-SEC-004 |
| **Description** | Document upload security (type/size and related controls) is addressed when upload is implemented. |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P1 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Upload path enforces basic type/size limits; malware scanning may be deferred with explicit note. |
| **Implementation phase** | 3+ |
| **Test strategy** | Security review + upload tests |
| **Evidence** | Security backlog / upload tests |
| **Status** | deferred |

### REQ-SEC-005

| Field | Value |
|-------|-------|
| **ID** | REQ-SEC-005 |
| **Description** | Dependency pinning strategy is defined before application dependencies are added. |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P1 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Strategy documented; lockfiles enforced when the stack appears. |
| **Implementation phase** | 2 |
| **Test strategy** | Doc review; lockfile presence later |
| **Evidence** | Security baseline docs |
| **Status** | planned |

### REQ-DATA-004

| Field | Value |
|-------|-------|
| **ID** | REQ-DATA-004 |
| **Description** | Retention and PII handling expectations are documented (implementation may be minimal in Part 1). |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P1 |
| **Scope** | Both |
| **Acceptance criteria** | Security/ops docs state how document data should be treated. |
| **Implementation phase** | 1–5 |
| **Test strategy** | Doc review |
| **Evidence** | Security / operations docs |
| **Status** | planned |

---

## Counts (this file)

| Category | Count |
|----------|-------|
| REQ-AI (005–006) | 2 |
| REQ-OBS | 4 |
| REQ-TEST | 4 |
| REQ-DEPLOY | 4 |
| REQ-DOC | 4 |
| REQ-SEC | 5 |
| REQ-DATA-004 | 1 |
| **Total** | **24** |

Part 2 forward-compatibility NFRs that preserve extension points are listed in [part-2-forward-compatibility.md](./part-2-forward-compatibility.md).
