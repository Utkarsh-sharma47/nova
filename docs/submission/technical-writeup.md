# Nova — Technical Write-up (GoComet Deliverable 3)

| Field | Value |
|-------|-------|
| Audience | GoComet technical reviewers |
| Length | 1–2 pages equivalent |
| Diagram | [architecture-diagram.md](./architecture-diagram.md) |
| PRD | [prd.md](./prd.md) |

---

## Architecture & data flow

```text
User → React UI → FastAPI → Ingestion → Document Storage
                              ↓
                     DocumentProcessorPort (PDF / text / PNG / JPEG)
                              ↓
                     Extractor (LLMPort: MockLLM | OpenAI-compatible vision/text)
                              ↓
                     Validator (deterministic rules + optional LLM)
                              ↓
                     Router (policy + hard AUTO_APPROVE constraints)
                              ↓
                     PostgreSQL (system of record + append-only AI history)
                              ↓
                     Query Service (allow-listed intents) → UI / ops
```

Observability: structured JSON logs with `request_id` / `trace_id` / `run_id` / `agent_execution_id`, plus `/health`, `/ready`, `/metrics`.

State persistence: document lifecycle + verification run + append-only extractions, validations, decisions. Ingest is idempotent via `Idempotency-Key`.

Part 2 extension points (not implemented): email ingestion, multi-doc validation, approval actions, outbound communication — see `docs/architecture/part2-extension-points.md`.

---

## Three nastiest failure modes (and how Nova handles them)

1. **Hallucinated “KNOWN” fields**  
   Risk: model invents HS code / ports.  
   Mitigation: schema invariants (KNOWN ⇒ evidence); heuristic MockLLM never invents; normalization downgrades fabricated snippets; extractor eval fabrication gate = 0.

2. **Silent AUTO_APPROVE under uncertainty**  
   Risk: missing/uncertain validation still approves.  
   Mitigation: router safety constraints + contract-level forbids; decision eval `false_auto_approve_count = 0`.

3. **Vision/image documents without readable text**  
   Risk: empty OCR → fake values.  
   Mitigation: images accepted via `RasterImageAdapter`; without live vision credentials MockLLM returns MISSING (not invented); live OpenAI adapter may read images when configured.

---

## Testing evidence (run locally)

```bash
ruff check src tests && mypy && pytest -q
cd frontend && npm ci && npm test && npm run typecheck && npm run build
PYTHONPATH=src python scripts/run_full_evaluation.py
docker compose up --build
```

Authoritative gates in `scripts/run_full_evaluation.py`:

- Decision: `false_auto_approve_count = 0`
- Extractor: `fabrication_count = 0`
- Validator: `unsafe_match_count = 0`

Reports: `docs/evaluation/reports/*-latest.json`.

---

## Observability & shipment traceability

Every stage carries shipment/document/run/trace IDs. UI links document ↔ shipment. Ops summary shows pipeline counts from the API (no fake demo state). Prometheus metrics at `/metrics`.

---

## Cost / document & latency bottleneck

| Mode | Cost / document | Latency bottleneck |
|------|-----------------|--------------------|
| MockLLM (default CI/demo) | ~$0 (synthetic tokens) | Local CPU + Postgres I/O |
| Live OpenAI-compatible | Provider tokens × pages/images | **LLM round-trips** (extractor dominant) |

Optimization strategy: keep MockLLM for CI; use live vision only when needed; truncate document text in prompts; bounded retries (max 2); fail closed instead of long retry storms; prefer deterministic validator over LLM judgment.

Benchmark helper: `scripts/benchmark_pipeline.py` (MockLLM). Live $ numbers require `LLM_PROVIDER=openai` + `LLM_API_KEY` and should be recorded during pilot week — not fabricated here.

---

## What would change with one week instead of one day

With **one day**: ship fail-closed pipeline, assignment fields, image accept + MockLLM safety, document preview UI, submission PRD/write-up, eval gates.

With **one week**: customer-specific rules authoring UX, richer extractor golden set (scanned PDFs/OCR), live cost dashboards, time-bounded ops SLOs, production remote deploy evidence, deeper CG shadow-mode comparison vs human decisions.

---

## Assignment coverage snapshot

| Deliverable | Status |
|-------------|--------|
| D1 PRD (this folder) | Present |
| D2A Extractor fields + images/vision path | Implemented (live vision optional) |
| D2B Validator | Implemented |
| D2C Router | Implemented |
| D2D Storage + grounded query (+ week window) | Implemented |
| D2E UI with real document + backend state | Implemented |
| D3 Technical write-up + diagram | Present |
