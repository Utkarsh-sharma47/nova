# Traceability matrix

Maps every stable requirement to design, implementation phase, test, and evidence.

**Auditor rule:** A requirement may be marked `done` only when Design, Test, and Evidence cells are populated with concrete artifacts a reviewer can open or re-run.

## Status legend

| Status | Meaning |
|--------|---------|
| documented | Specified; implementation not started |
| planned | Implementation phase known; not started |
| in_progress | Actively being built |
| done | Implemented + tested + evidenced |
| deferred | Explicitly postponed with rationale |

## Design artifact placeholders

Until architecture/agents/database docs exist, Design points to the intended future path. Phase 1 product/requirements docs satisfy design for documentation-only REQs.

| Code | Intended artifact |
|------|-------------------|
| D-PROD | `docs/product/*` |
| D-SCOPE | `docs/requirements/scope.md`, `part-2-forward-compatibility.md` |
| D-ARCH | Architecture / principles / extension-points docs |
| D-AGENT | Agent contracts (extractor, validator, router) |
| D-DATA | Database / ERD docs |
| D-API | API docs |
| D-UI | UI feature docs |
| D-OBS | Observability docs |
| D-TEST | Testing philosophy + suites |
| D-CI | CI/CD workflows + deploy docs |
| D-SEC | Security baseline |
| D-ADR | Architecture decision records |
| D-DEMO | Demo / submission runbook |

---

## Matrix

| Requirement | Source | Scope | Design | Implementation phase | Test | Evidence | Status |
|-------------|--------|-------|--------|----------------------|------|----------|--------|
| REQ-PROD-001 | ASSIGNMENT | Part 1 | D-PROD | 1 / demo 7 | Doc + demo review | `docs/product/nova.md`, demo notes | documented |
| REQ-PROD-002 | ASSIGNMENT | Part 1 | D-PROD | 1 | Doc review | `docs/product/problem-statement.md` | documented |
| REQ-PROD-003 | ASSIGNMENT | Part 1 | D-ARCH, D-AGENT | 2→4 | Design + golden + failure | Router policy; fixtures | documented |
| REQ-PROD-004 | ASSIGNMENT | Both | D-SCOPE, D-AGENT | 4 / Part 2 UX | Design + golden | Router contract; Part 2 doc | documented |
| REQ-EXT-001 | ASSIGNMENT | Part 1 | D-ARCH, D-API | 3 | Integration | Ingestion contract; run log | planned |
| REQ-EXT-002 | ASSIGNMENT | Part 1 | D-AGENT | 3 | Unit + golden | Extraction schema; sample output | planned |
| REQ-EXT-003 | ASSIGNMENT | Part 1 | D-AGENT | 3 | Contract + eval | Schema; eval report | planned |
| REQ-EXT-004 | ASSIGNMENT | Part 1 | D-AGENT, D-UI | 3 | Contract + review checklist | Evidence payloads | planned |
| REQ-EXT-005 | ASSIGNMENT | Part 1 | D-TEST | 5 | Eval harness | Fixtures + eval artifacts | planned |
| REQ-EXT-006 | ENGINEERING | Part 1 | D-AGENT, D-OBS | 3–4 | Failure tests | Failure results | planned |
| REQ-VAL-001 | ASSIGNMENT | Part 1 | D-AGENT | 4 | Unit + fixtures | Rules format + tests | planned |
| REQ-VAL-002 | ASSIGNMENT | Part 1 | D-AGENT | 4 | Golden | Golden fixtures | planned |
| REQ-VAL-003 | ASSIGNMENT | Part 1 | D-AGENT | 4 | Golden | Golden fixtures | planned |
| REQ-VAL-004 | ASSIGNMENT | Part 1 | D-AGENT | 4 | Golden | Golden fixtures | planned |
| REQ-VAL-005 | ENGINEERING | Part 1 | D-AGENT, D-ADR | 2–4 | Design + unit | ADR + validator tests | planned |
| REQ-VAL-006 | ENGINEERING | Part 1 | D-DATA, D-API | 4–5 | Integration | Audit fields sample | planned |
| REQ-ROUTER-001 | ASSIGNMENT | Part 1 | D-AGENT | 4 | Golden | Policy + fixtures | planned |
| REQ-ROUTER-002 | ASSIGNMENT | Part 1 | D-AGENT | 4 | Golden | Policy + fixtures | planned |
| REQ-ROUTER-003 | ASSIGNMENT | Part 1 | D-AGENT | 4 | Golden | Policy + fixtures | planned |
| REQ-ROUTER-004 | ENGINEERING | Part 1 | D-AGENT | 2–4 | Design + unit | Router policy doc + tests | planned |
| REQ-ROUTER-005 | ENGINEERING | Part 1 | D-AGENT | 4 | Failure | Failure fixtures | planned |
| REQ-DATA-001 | ASSIGNMENT | Part 1 | D-DATA, D-API | 5 | Integration | Schema + API | planned |
| REQ-DATA-002 | ENGINEERING | Both | D-DATA | 2–5 | Schema review | ERD | planned |
| REQ-DATA-003 | ENGINEERING | Part 1 | D-DATA, D-API | 5 | Integration | Idempotency tests | planned |
| REQ-DATA-004 | ENGINEERING | Both | D-SEC | 1–5 | Doc review | Security/ops docs | planned |
| REQ-QUERY-001 | ASSIGNMENT | Part 1 | D-API | 5–6 | Integration | API examples | planned |
| REQ-QUERY-002 | ASSIGNMENT | Part 1 | D-API, D-AGENT | 6 | Integration + eval | Query examples + traces | planned |
| REQ-QUERY-003 | ENGINEERING | Part 1 | D-API, D-TEST | 6 | Adversarial eval | Eval cases | planned |
| REQ-UI-001 | ASSIGNMENT | Part 1 | D-UI | 6 | Smoke + manual | Screenshots / demo | planned |
| REQ-UI-002 | ENGINEERING | Part 1 | D-UI | 6 | Manual checklist | Checklist + screenshots | planned |
| REQ-UI-003 | ENGINEERING | Both | D-UI, D-SCOPE | 6 | Manual checklist | Screenshots | planned |
| REQ-AI-001 | ASSIGNMENT | Part 1 | D-AGENT | 3 | Contract | Agent docs + suite | planned |
| REQ-AI-002 | ASSIGNMENT | Part 1 | D-AGENT | 4 | Contract + golden | Agent docs + suite | planned |
| REQ-AI-003 | ASSIGNMENT | Part 1 | D-AGENT | 4 | Contract + golden | Agent docs + suite | planned |
| REQ-AI-004 | ENGINEERING | Part 1 | D-AGENT, D-TEST | 3–4 | Eval | Eval report | planned |
| REQ-AI-005 | ENGINEERING | Part 1 | D-AGENT, D-OBS | 3–4 | Unit/integration | Config + failure tests | planned |
| REQ-AI-006 | ENGINEERING | Part 1 | D-OBS, D-DATA | 3–5 | Integration | Metadata samples | planned |
| REQ-OBS-001 | ENGINEERING | Part 1 | D-OBS | 3–5 | Integration | Log samples | planned |
| REQ-OBS-002 | ASSIGNMENT/ENG | Part 1 | D-OBS | 3–5 | Integration | Trace samples | planned |
| REQ-OBS-003 | ENGINEERING | Part 1 | D-OBS | 3–5 | Integration | Metrics sample | planned |
| REQ-OBS-004 | ASSIGNMENT/ENG | Part 1 | D-OBS | 4–5 | Failure | Error taxonomy + fixtures | planned |
| REQ-TEST-001 | ENGINEERING | Part 1 | D-TEST, D-CI | 3+ | CI | CI logs | planned |
| REQ-TEST-002 | ENGINEERING | Part 1 | D-TEST | 4–5 | CI golden | Test report | planned |
| REQ-TEST-003 | ENGINEERING | Part 1 | D-TEST, D-CI | 1+ | CI review | Workflow review | documented |
| REQ-TEST-004 | ENGINEERING | Part 1 | D-TEST, D-AGENT | 3–4 | CI contract | Contract report | planned |
| REQ-DEPLOY-001 | ENGINEERING | Part 1 | D-CI | 1 | CI | Workflow runs | planned |
| REQ-DEPLOY-002 | ENGINEERING | Part 1 | D-CI | 1 | Review | CI docs | planned |
| REQ-DEPLOY-003 | ENGINEERING | Part 1 | D-CI | 7 | Smoke | Deploy docs | planned |
| REQ-DEPLOY-004 | ENGINEERING | Part 1 | D-CI | 1→7 | CI growth | Roadmap + workflows | planned |
| REQ-DOC-001 | ASSIGNMENT | Part 1 | D-PROD + docs tree | 1+ | Doc structure review | `docs/` | documented |
| REQ-DOC-002 | ENGINEERING | Part 1 | D-ADR / AGENTS | 1 | Doc review | `AGENTS.md` / governance | planned |
| REQ-DOC-003 | ENGINEERING | Both | D-ADR | 1+ | Doc review | ADR files | planned |
| REQ-DOC-004 | ASSIGNMENT | Part 1 | D-DEMO | 7 | Manual runbook | Demo runbook | planned |
| REQ-SEC-001 | ENGINEERING | Part 1 | D-SEC | 1 | Ignore/secret check | `.gitignore`, `.env.example` | planned |
| REQ-SEC-002 | ENGINEERING | Part 1 | D-SEC | 1+ | Secret scan | CI logs | planned |
| REQ-SEC-003 | ENGINEERING | Part 1 | D-SEC | 1→5 | Policy + later tests | Security docs | planned |
| REQ-SEC-004 | ENGINEERING | Part 1 | D-SEC | 3+ | Security review | Upload tests / backlog | deferred |
| REQ-SEC-005 | ENGINEERING | Part 1 | D-SEC | 2 | Doc review | Security docs | planned |
| REQ-SUBMISSION-001 | ASSIGNMENT | Part 1 | D-DEMO | 7 | Demo script | Demo notes | planned |
| REQ-SUBMISSION-002 | ASSIGNMENT | Part 1 | D-TEST, D-DEMO | 5–7 | Eval command | Eval artifacts | planned |
| REQ-SUBMISSION-003 | ASSIGNMENT | Part 1 | D-DEMO | 7 | Demo script | Demo notes | planned |
| REQ-PART2-001 | ASSIGNMENT | Part 2 | D-ARCH | 1–2 design | Design review | Extension-points doc | documented |
| REQ-PART2-002 | ASSIGNMENT | Part 2 | D-ARCH | 1–2 design | Design review | Extension-points doc | documented |
| REQ-PART2-003 | ASSIGNMENT | Part 2 | D-DATA | 2–5 schema | Schema review | ERD | planned |
| REQ-PART2-004 | ASSIGNMENT | Part 2 | D-ARCH, D-AGENT | 1–4 design | Design review | Extension-points doc | documented |
| REQ-PART2-005 | ASSIGNMENT | Part 2 | D-ARCH | 1–2 design | Design review | Extension-points doc | documented |
| REQ-PART2-006 | ASSIGNMENT | Part 2 | D-ARCH, D-DATA | 1–5 design | Design review | Extension-points doc | documented |
| REQ-PART2-007 | ASSIGNMENT | Part 2 | D-ARCH | 1–2 design | Design review | Extension-points doc | documented |

---

## Coverage summary

| Category | REQ count | Assignment | Engineering |
|----------|-----------|------------|-------------|
| REQ-PROD | 4 | 4 | 0 |
| REQ-EXT | 6 | 5 | 1 |
| REQ-VAL | 6 | 4 | 2 |
| REQ-ROUTER | 5 | 3 | 2 |
| REQ-DATA | 4 | 1 | 3 |
| REQ-QUERY | 3 | 2 | 1 |
| REQ-UI | 3 | 1 | 2 |
| REQ-AI | 6 | 3 | 3 |
| REQ-OBS | 4 | 2* | 2* |
| REQ-TEST | 4 | 0 | 4 |
| REQ-DEPLOY | 4 | 0 | 4 |
| REQ-DOC | 4 | 2 | 2 |
| REQ-SEC | 5 | 0 | 5 |
| REQ-SUBMISSION | 3 | 3 | 0 |
| REQ-PART2 | 7 | 7 | 0 |
| **Total** | **68** | | |

\*REQ-OBS-002 and REQ-OBS-004 are dual-sourced (assignment observability/failure handling + engineering detail).

## Final audit procedure

1. Filter matrix to **ASSIGNMENT** + **Scope = Part 1** (and Both where Part 1 obligations exist).
2. Confirm each row has non-placeholder Design, Test, and Evidence.
3. Re-run cited tests or open cited artifacts.
4. Confirm no Part 2 feature is required for Part 1 pass.
5. Sign [acceptance-criteria.md](./acceptance-criteria.md) auditor block.

## Update protocol

When a requirement is implemented:

1. Set Status → `in_progress` then `done`.
2. Replace Design placeholders with concrete paths.
3. Link Test job/name and Evidence path/command.
4. Keep IDs stable; never reuse IDs for different meaning.
