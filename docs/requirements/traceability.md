# Requirement traceability

Maps requirements to design artifacts, planned tests, and evidence. Update when implementation phases land.

| REQ ID | Design artifact | Test type | Evidence location | Phase |
|--------|-----------------|-----------|-------------------|-------|
| REQ-PROD-001–004 | `docs/product/*`, principles | Doc review | Product docs | 1 |
| REQ-EXT-001–006 | Agent extractor contract (future `docs/agents/`), ingestion port | Unit, integration, failure | Fixtures + traces | 3–5 |
| REQ-VAL-001–006 | Validator design, rules format | Golden / unit | Rules fixtures | 4–5 |
| REQ-ROUTER-001–005 | Router policy doc | Golden / failure | Policy fixtures | 4–5 |
| REQ-DATA-001–004 | ERD / `docs/database/` (future) | Integration | Migrations + API | 5 |
| REQ-QUERY-001–003 | Query API + NL query design | Integration + eval | Query eval set | 5–6 |
| REQ-UI-001–003 | UI feature doc | Smoke / manual | Screenshots / demo | 6 |
| REQ-AI-001–006 | `docs/agents/`, AI governance | Contract + eval | Agent docs + eval | 3–5 |
| REQ-OBS-001–004 | Observability philosophy | Integration | Log/trace samples | 3–5 |
| REQ-TEST-001–004 | Testing philosophy | CI | CI logs | 1 / 3+ |
| REQ-DEPLOY-001–004 | `docs/deployment/ci-cd.md` | CI | Workflow runs | 1 / 7 |
| REQ-DOC-001–004 | `docs/**`, `AGENTS.md` | Docs structure script | Repo tree | 1 / 7 |
| REQ-SEC-001–005 | Security baseline | Secret scan script | CI + `.gitignore` | 1+ |
| REQ-SUBMISSION-001–003 | Ops demo runbook (future) | Demo script | Demo notes | 7 |
| REQ-PART2-001–007 | `docs/architecture/part2-extension-points.md` | Design review | Extension points doc | 1–2 |

## Traceability rules

1. Every P0 Part 1 requirement must have a design pointer before coding starts.
2. Every implemented requirement must have a test pointer before claiming done.
3. Evidence must be reproducible by a reviewer from the repository or documented commands.
