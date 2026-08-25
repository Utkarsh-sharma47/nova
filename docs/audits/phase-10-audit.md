# Phase 10 audit — Full system E2E, failure testing, AI regression, quality verification

| Field | Value |
|-------|-------|
| Date | 2026-08-25 |
| Auditor | Principal QA, Reliability, and AI Evaluation Engineer |
| Scope | Part 1 end-to-end verification across Phases 3–9 |
| Branch | `feature/phase-10-system-verification` |
| Related docs | `docs/testing/phase-10-system-verification.md`, `TESTING.md`, evaluation reports |
| Verdict | **PASS WITH LIMITATIONS** |

## 1. Scope

Verified Nova as one Part 1 application:

```text
Frontend → POST /v1/documents → ingestion → processing → Extractor →
Validator → Router → PostgreSQL → Document/Shipment APIs → Query API → UI
```

**In scope:** E2E matrix (33 cases), AI evaluation gates, failure injection,
security regression, data integrity, API contract smoke, performance baselines
(MockLLM), Docker Compose clean deploy, CI hardening.

**Out of scope:** Architecture redesign, new product features, live vendor LLM
quality, browser Playwright automation, Part 2 workflows.

**Trust rule:** Results below were executed in this audit; no fabricated metrics.

## 2. Environment

| Item | Value |
|------|-------|
| Python | 3.12 (`.venv`) |
| Node | frontend Vitest 4.x |
| LLM | MockLLM only |
| Local DB tests | SQLite (default pytest) |
| Docker smoke | Compose `db`+`api`+`web`, clean volumes, ports 35432/38000/38080 |
| Alembic head | `0004_phase7_pipeline` |

## 3. Test matrix results

Canonical suite: `tests/e2e/test_phase10_matrix.py` (33 cases) + integrity + API smoke.

| Command | Result |
|---------|--------|
| `pytest -q tests/e2e/` | **36 passed** |
| `pytest -q` (full) | **205 passed, 2 skipped** |
| Frontend `npm test` | **25 passed** (5 files) |
| `ruff check src tests` | **All checks passed** |
| `mypy` | **Success: 95 source files** |

Matrix coverage includes valid invoice/BoL, UNKNOWN/AMBIGUOUS/MISMATCH/UNCERTAIN,
HUMAN_REVIEW / AMENDMENT_REQUEST / AUTO_APPROVE, agent/LLM failures, corrupt /
unsupported / oversized / traversal / MIME mismatch, idempotency, failsafe,
unsafe AUTO_APPROVE override, and query grounded + security cases.

## 4. AI evaluation

Command: `python scripts/run_full_evaluation.py`

| Suite | n | Safety metric | Result |
|-------|---|---------------|--------|
| Validator eval | 16 | `unsafe_match_count=0` | PASS |
| Validator regression | 15 | `unsafe_match_count=0` | PASS |
| Decision / Router | 22 | `false_auto_approve_count=0`, rate `0.000`, gate passed | PASS |
| Extractor fabrication contracts | pytest subset | fabrication invariants asserted | PASS |

Reports: `docs/evaluation/reports/{validator-eval,validator-regression,decision-eval}-latest.json`.

**Note:** Extractor does not yet have a labeled field-accuracy harness; fabrication=0
is enforced via contract/unit gates already defined in-repo (not invented as an SLO).

## 5. Failure testing

Controlled injection covered in matrix + existing suites:

| Fault | Observed fail-closed behavior |
|-------|-------------------------------|
| Extractor / LLM provider error | No decision; extraction FAILED |
| Validator persistence failure | Not AUTO_APPROVE |
| Router exception | Document `failed` |
| Malformed LLM / timeout | Extraction FAILED; no decision |
| system_failsafe | HUMAN_REVIEW + `system_failsafe` actor |
| Unsafe LLM AUTO_APPROVE suggestion | Overridden; not AUTO_APPROVE |
| DB write failure helper | Raises; no silent success |

## 6. Security testing

| Check | Result |
|-------|--------|
| Path traversal filename | Rejected (`UNSAFE_FILENAME`) or sanitized without `..` |
| Oversized upload | 413 `PAYLOAD_TOO_LARGE` |
| Unsupported / MIME mismatch | 422 structured errors; no stack/token leakage |
| Query SQL / prompt injection | `UNSUPPORTED` + `SECURITY_REJECTED` |
| Secret pattern script | PASSED |
| Frontend XSS rendering | Text escaped; no script execution (Vitest) |

## 7. Performance (local MockLLM baseline — not production)

`scripts/benchmark_pipeline.py` (n=5, SQLite/TestClient):

| Stage | mean | p50 | max |
|-------|------|-----|-----|
| Full pipeline total | 16.4 ms | 16.0 ms | 18 ms |
| Extraction | 5.8 ms | 6.0 ms | 7 ms |
| Validation | 2.4 ms | 2.0 ms | 3 ms |
| Routing | 0.0 ms | 0.0 ms | 0 ms |

`scripts/benchmark_document_processing.py`: text invoice ~0.4 ms; PDF 1–5 pages ~1.4–3.5 ms.

No production SLO claim. No obvious regression vs Phase 7 MockLLM baseline order-of-magnitude.

## 8. Docker / deployment

Clean volumes via `docker compose --env-file … up --build`:

| Check | Result |
|-------|--------|
| `docker compose build` | PASS |
| `/health` | `{"status":"ok"}` |
| `/ready` | database + object_storage ok |
| `/metrics` | HTTP 200 |
| Frontend `:38080` | HTTP 200 |
| Upload → document | `status=DECIDED`, extraction present |
| `alembic current` | `0004_phase7_pipeline (head)` |
| `alembic upgrade head` ×2 | Idempotent (no-op) |

## 9. CI

`.github/workflows/ci.yml` updated:

- Migration head assert → `0004_phase7_pipeline` (+ agent/decision/validation tables)
- `python scripts/run_full_evaluation.py` gate
- Frontend job: `npm ci`, typecheck, Vitest, build

Preserved: docs structure, secret patterns, Ruff, MyPy, pytest, API image build.

**CI on GitHub Actions for this PR:** not observed as green in this audit session
(remote CI runs after push). Local equivalents of CI checks were executed above.

## 10. Known limitations

1. No Playwright/browser E2E — UI verified via Vitest workflow tests + API E2E.
2. No live vendor LLM evaluation (MockLLM only) — intentional for Part 1 CI.
3. Extractor field-accuracy labeled harness still absent; fabrication gated by contracts.
4. Performance numbers are local MockLLM/SQLite — not production capacity claims.
5. Concurrent agent branch interference observed during development; audit uses restored Phase 10 tree.

## 11. Requirements coverage

See updated [`docs/requirements/traceability.md`](../requirements/traceability.md)
Phase 10 evidence section. Gaps remaining as design/deferrals only where already
documented (e.g. live LLM, Part 2, browser E2E).

## 12. Quality gate assessment

| Gate | Status |
|------|--------|
| Critical E2E flow | PASS (matrix + Docker smoke) |
| False AUTO_APPROVE | **0** on decision eval |
| Unsafe MATCH | **0** on validator eval/regression |
| Data integrity | PASS (append-only / idempotent replay tests) |
| Local static + pytest | PASS |
| Clean Docker deploy | PASS |
| Documented API smoke | PASS |
| Serious security regression | None observed |

## 13. Verdict

**PASS WITH LIMITATIONS** — Part 1 system verification succeeds under MockLLM with
documented UI/browser and live-LLM limitations that do not invalidate Part 1
correctness or safety gates.
