# Known limitations — Part 1 final release

Honest inventory of what is complete, partial, engineering-limited, deferred, or Part 2.

## 1. Required and complete

- End-to-end Part 1 pipeline: upload → process → extract → validate → route → persist → query → UI
- Invoice and Bill of Lading document types
- Confidence + evidence on extracted fields
- MATCH / MISMATCH / UNCERTAIN validation outcomes
- AUTO_APPROVE / HUMAN_REVIEW / AMENDMENT_REQUEST routing with fail-closed safety
- Append-only extraction / validation / decision history (PostgreSQL + Alembic)
- Grounded `POST /v1/query` without arbitrary SQL
- Minimal ops UI against real APIs
- Clean + messy synthetic samples and recorded evaluation reports
- Local Docker Compose deploy path
- CI for docs, secrets, backend, frontend, migrations, image builds

## 2. Required but partial

| Item | Notes |
|------|-------|
| `REQ-SEC-004` malware scanning | MIME/size/path controls exist; antivirus/malware scanning is **not** implemented |
| Live vendor LLM | `LLMPort` + optional OpenAI-compatible adapter; default is **MockLLM**. Without `LLM_API_KEY`, falls back to mock |
| Images / vision | PNG/JPEG accepted; vision extraction requires live provider. Mock path returns MISSING (no fabrication) |
| Scanned PDF OCR | Digital PDF text only; dedicated OCR adapter deferred |
| Customer rule authoring UI | Default presence rules + request rules; no rich ruleset editor |
| `audit_events` table | Audit/event **contracts** exist; dedicated `audit_events` persistence table is not migrated |

## 3. Engineering limitations

- Shared browser-visible API key for Part 1 ops UI (accepted model; not multi-user RBAC)
- `pip-audit` findings logged as CI warnings (not hard-fail)
- No managed backup service beyond named Docker volumes + recovery runbook
- Query intents are allow-listed (by design) — not a general analytics chatbot
- OCR / scanned PDF / Office formats out of Part 1 document-processing scope
- Orphan `__pycache__` under empty `tests/e2e/` / `tests/ops/` cleaned in Phase 12; primary e2e coverage lives in `tests/pipeline/`

## 4. Intentionally deferred

- Malware scanning of uploads
- Hard-fail dependency audit gate
- Full multi-tenant auth / SSO / per-user authorization
- Managed cloud backups and multi-region HA
- Remote production host deployment evidence (procedure exists; execution **NOT EXECUTED**)

## 5. Part 2 — PLANNED, NOT IMPLEMENTED IN PART 1

| Capability | Status |
|------------|--------|
| Email ingestion | PLANNED |
| Multiple attachments / multi-doc workflows | PLANNED (schema 1:N ready) |
| Cross-document verification | PLANNED |
| Human review approval actions / workflow UX | PLANNED (HUMAN_REVIEW decision exists) |
| Amendment outbound workflow | PLANNED |
| Draft replies / outbound communication | PLANNED |
| Additional ingestion channels | PLANNED |

See [`../architecture/part2-extension-points.md`](../architecture/part2-extension-points.md).

## Non-claims

- Do not claim remote production deployment was executed.
- Do not claim live LLM accuracy on real customer documents.
- Do not claim Part 2 features are implemented.
