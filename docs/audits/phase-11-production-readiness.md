# Phase 11 audit — Deployment, security hardening, observability, production readiness

| Field | Value |
|-------|-------|
| Date | 2026-08-25 |
| Scope | Containerization, configuration, database migrations, CI/CD, security hardening, observability, recovery, deployment docs |
| Auditor | Principal DevOps / Production Reliability Engineer |
| Branch | `feature/phase-11-production-hardening` (impl worktree `feature/phase-11-impl`) |
| Verdict | **PASS** for local reproducibility; remote host deploy **NOT EXECUTED** |

## 1. Scope

Phase 11 makes Part 1 reproducibly deployable via Docker Compose without redesigning application architecture and without Kubernetes/Kafka/microservices.

## 2. Checklist

| ID | Item | Status | Evidence |
|----|------|--------|----------|
| C-01 | Backend production image builds (non-root) | PASS | `docker build -t nova-api:phase11 .` (UID 10001, STOPSIGNAL) |
| C-02 | Frontend production image builds (non-root, no baked auth secret) | PASS | `nginxinc/nginx-unprivileged`; no `VITE_API_AUTH_TOKEN` build ARG |
| C-03 | Compose clean startup (api+db+web) | PASS | Compose project nova_p11v3 healthy |
| C-04 | Health / ready / metrics | PASS | /health /ready /metrics + web / |
| C-05 | Alembic clean upgrade + upgrade again | PASS | CI workflow + local head `0004_phase7_pipeline` |
| C-06 | Persistent volumes retained across restart | PASS | restarts retained volumes; stack recovered |
| C-07 | No `create_all` in production path | PASS | `create_all` only in tests/scripts; runtime uses Alembic |
| C-08 | `.env.example` documents required vars | PASS | root + `docs/deployment/configuration.md` |
| C-09 | Startup rejects placeholder/weak production config | PASS | unit tests in `tests/unit/test_phase3_foundation.py` |
| C-10 | CI lint/type/tests/secrets/frontend/Docker | PASS | `.github/workflows/ci.yml` updated (local parity run) |
| C-11 | Secret scan clean | PASS | `./scripts/check-secret-patterns.sh` |
| C-12 | Dependency audit run | PASS | `pip-audit` (pytest advisory logged); `npm audit` 0 vulns |
| C-13 | CORS allow-list (no prod wildcard) | PASS | production `Settings.validate_runtime` |
| C-14 | Upload / request size limits | PASS | `MAX_*` + `RequestSizeLimitMiddleware` + test |
| C-15 | Path-safe document storage | PASS | existing traversal tests |
| C-16 | Safe error envelopes (no stack traces) | PASS | `app.py` unhandled handler |
| C-17 | Structured logs with request/trace/(run\|agent) IDs | PASS | JsonFormatter + stage loggers |
| C-18 | API / DB / web restart recovery | PASS | sequential restart of api/db/web recovered ready |
| C-19 | Failed migration fails startup | PASS | `scripts/entrypoint.sh` `set -eu` + `alembic upgrade head` |
| C-20 | Temporary DB unavailability → not_ready | PASS | `/ready` + `pool_pre_ping` (existing behavior) |
| C-21 | Evaluation suite false AUTO_APPROVE = 0 | PASS | `test_decision_evaluation_zero_false_auto_approve` PASSED |
| C-22 | Remote production host deployment | NOT EXECUTED | no host credentials |
| C-23 | `git diff --check` | PASS | clean |
| C-24 | ruff / mypy / pytest / frontend checks | PASS | ruff OK; mypy OK; pytest 173 passed + 2 skipped; frontend 24 tests + build |

## 3. Security findings

| ID | Severity | Finding | Disposition |
|----|----------|---------|-------------|
| S-01 | Medium | Web image previously baked auth token into JS layers | **Fixed** — runtime `/runtime-config.js` |
| S-02 | Low | Frontend container ran privileged nginx on :80 | **Fixed** — nginx-unprivileged :8080 |
| S-03 | Low | Production weak DB password / short token possible | **Fixed** — production `Settings` rules |
| S-04 | Info | Shared browser API key still client-visible (Part 1 model) | **Accepted** — documented |
| S-05 | Info | Malware scanning not implemented | **Deferred** — `REQ-SEC-004` |
| S-06 | Info | pip-audit: pytest 8.4.2 advisory PYSEC-2026-1845 | **Accepted for CI** — logged; not a runtime dep |

## 4. Deployment architecture

Compose: `web` (nginx-unprivileged:8080) → `api` (FastAPI non-root:8000) → `db` (Postgres 16) + document volume. Auth for UI injected at container start, not image build.

## 5. Remaining limitations

- Remote production deploy **NOT EXECUTED**.
- pip-audit findings logged without hard-fail.
- Part 1 shared API key remains browser-visible by design.
- No managed backup service beyond named volumes + runbook.

## 6. Exact verification commands (local)

```text
ruff check src tests          → All checks passed
mypy                          → Success: no issues found in 95 source files
pytest -q                     → 173 passed, 2 skipped
frontend npm test/typecheck/build → 24 passed; build OK; npm audit 0
./scripts/check-docs-structure.sh → PASSED
./scripts/check-secret-patterns.sh → PASSED
tests/evaluation decision gate → false AUTO_APPROVE = 0 (PASSED)
```
