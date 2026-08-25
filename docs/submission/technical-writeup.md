# Nova — Technical Write-up (GoComet Deliverable 3)

| Field | Value |
|-------|-------|
| Audience | GoComet technical reviewers |
| Length | 1–2 pages equivalent |
| Diagram | [architecture-diagram.md](./architecture-diagram.md) |
| PRD | [prd.md](./prd.md) |

Quantitative claims are tagged **MEASURED**, **ESTIMATED**, or **PLANNED**. Live provider $ costs were **not measured** in this repository without a keyed production-like run.

---

## 1. Architecture

```text
User → React UI → FastAPI → Ingestion → Document Storage (FS)
                              ↓
                     DocumentProcessorPort (PDF / text / PNG / JPEG)
                              ↓
                     Extractor ← LLMPort (MockLLM | OpenAI-compatible vision/text)
                              ↓ ExtractionResult
                     Validator ← Rule Engine (deterministic-first)
                              ↓ ValidationResult
                     Router (policy + hard AUTO_APPROVE constraints)
                              ↓ DecisionResult
                     PostgreSQL (system of record + append-only AI history)
                              ↓
                     Query Service (allow-listed intents) → UI
```

Ports keep domain logic vendor-agnostic. Detail: [architecture-diagram.md](./architecture-diagram.md).

## 2. Agent boundaries

| Boundary | Rule |
|----------|------|
| Extractor | May call LLM/vision; may not decide disposition |
| Validator | Deterministic MISMATCH cannot be upgraded by LLM to MATCH |
| Router | Policy authoritative; advisory LLM cannot force `AUTO_APPROVE` |
| Query | No SQL generation; security reject for injection |

## 3. State and crash recovery

- Lifecycle: document + verification run statuses in PostgreSQL
- Append-only: extracted fields, validations, decisions
- Idempotent ingest: `Idempotency-Key` fingerprint replay
- Restart: durable IDs; no invented prior agent results
- Failures: structured `FAILED` / fail-closed `HUMAN_REVIEW`, not silent approve

## 4. Failure mode #1 — hallucinated KNOWN fields

**Risk:** invent HS code / ports.
**Mitigation:** Pydantic invariants (`KNOWN` ⇒ value + evidence); MockLLM heuristic never invents; fabricated snippets downgraded; extractor eval `fabrication_count = 0` (**MEASURED** offline).

## 5. Failure mode #2 — silent AUTO_APPROVE under uncertainty

**Risk:** missing/uncertain still approves.
**Mitigation:** router safety constraints + contract forbids; decision eval `false_auto_approve_count = 0` (**MEASURED** offline, n=22).

## 6. Failure mode #3 — image/vision without readable text

**Risk:** empty OCR → fake values.
**Mitigation:** `RasterImageAdapter` accepts PNG/JPEG; without live credentials MockLLM returns `MISSING` (not invented) (**MEASURED** in unit tests); live vision optional via OpenAI-compatible adapter (**ESTIMATED** quality when enabled).

## 7. Observability

Structured JSON logs with `request_id` / `trace_id` / `run_id` / `agent_execution_id`. Endpoints: `/health`, `/ready`, `/metrics`. UI ops summary uses live API counts. Shipment↔document links provide end-to-end traceability in the UI.

**Dashboard metrics available now:** pipeline status counts, decision mix via ops/query, Prometheus HTTP metrics. **PLANNED:** dedicated SRE cost/latency SLO dashboard with live $ burn.

## 8. Cost

| Item | Classification | Notes |
|------|----------------|-------|
| MockLLM CI/demo | **MEASURED** | ~$0 API spend; synthetic tokens only |
| Live OpenAI-compatible | **NOT MEASURED** here | Requires `LLM_API_KEY`; do not invent $ figures |
| Live cost drivers (**ESTIMATED** if enabled) | Input tokens (text + image tiles), output tokens, retries, vision pages |
| Cost controls | Mock default; truncate prompt text; max 2 extractor retries; fail closed; deterministic validator first |

## 9. Latency

| Item | Classification | Notes |
|------|----------------|-------|
| Bottleneck under MockLLM | **ESTIMATED** local | CPU + Postgres I/O dominate |
| Bottleneck under live LLM | **ESTIMATED** | Extractor LLM round-trips dominate |
| Optimization | Bound retries/timeouts; keep MockLLM in CI; vision only when needed; prefer deterministic validation |

Helper: `scripts/benchmark_pipeline.py` (MockLLM local). Treat outputs as **MEASURED local/test**, not production SLOs.

## 10. One-week vs one-day tradeoff

**One day:** fail-closed pipeline, assignment fields, image accept + MockLLM safety, document preview, submission docs, eval gates FA=0 / fabrication=0.
**One week:** richer customer-rule authoring UX, broader extractor goldens (scanned PDF/OCR), live cost dashboards, time-bounded ops SLOs, remote deploy evidence, CG shadow-mode vs human decisions (**PLANNED**).

---

## Testing evidence (**MEASURED** this audit run)

```bash
ruff check src tests && mypy src && pytest -q
cd frontend && npm test && npm run typecheck && npm run build
PYTHONPATH=src python scripts/run_full_evaluation.py
docker compose build
```

Gates from `scripts/run_full_evaluation.py`:

- Decision: `false_auto_approve_count = 0`
- Extractor: `fabrication_count = 0`
- Validator: `unsafe_match_count = 0`

Reports: `docs/evaluation/reports/*-latest.json`.
