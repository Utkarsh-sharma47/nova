# Roadmap (detail)

Canonical high-level status: [`../../ROADMAP.md`](../../ROADMAP.md).

## Phase 1 — Engineering foundation

**Status:** Complete.

## Phase 2 — Stack selection & contracts

**Status:** Complete. Audit: [`../audits/phase-2-audit.md`](../audits/phase-2-audit.md).

## Phase 3 — Application foundation + document ingestion

**Status:** Complete. Audit: [`../audits/phase-3-audit.md`](../audits/phase-3-audit.md).

## Phase 4 — Extractor Agent

**Status:** Complete (`ExtractorService`, MockLLM, append-only extraction persistence).

## Phase 5 — Validator Agent + evaluation

**Status:** Complete. Audit: [`../audits/phase-5-audit.md`](../audits/phase-5-audit.md).

## Phase 6 — Router / Decision Agent

**Status:** Complete. Audit: [`../audits/phase-6-audit.md`](../audits/phase-6-audit.md).

## Phase 7 — End-to-end pipeline integration

**Status:** Complete (`PipelineOrchestrator`, validations table, wired HTTP reads).

## Phase 8 — Grounded Query API

**Status:** Complete (`POST /v1/query`, no LLM SQL).

## Phase 9 — Part 1 operations UI

**Status:** Complete (`frontend/`, Compose `web`).

## Phase 10–11 — Verification & production hardening

**Status:** Complete locally. Remote deploy **NOT EXECUTED**.
Audit: [`../audits/phase-11-production-readiness.md`](../audits/phase-11-production-readiness.md).

## Phase 12 — Final Part 1 release

**Status:** Complete — **PASS WITH LIMITATIONS**.
Artifacts: [`../audits/final-part1-audit.md`](../audits/final-part1-audit.md), [`../operations/demo-runbook.md`](../operations/demo-runbook.md).

## Part 2 — Forward

**PLANNED — NOT IMPLEMENTED IN PART 1.**

Email/file triggers, multi-attachment, cross-document validation, draft replies, human approval actions, outbound sending.
