# Part 1 end-to-end verification pipeline

**Status:** Implemented (Phase 7)  
**Package:** `nova.application.pipeline`

## Architecture

```text
POST /v1/documents
    → IngestionService (persist document + queued run; thin HTTP route)
    → PipelineOrchestrator
         → ExtractionApplicationService → ExtractorService → ExtractionResult
         → ValidatorAgent → ValidationResult (SQL validations, append-only)
         → RouterService → DecisionResult (SQL decisions, append-only)
    → document status DECIDED | FAILED
```

Orchestration lives in the application layer. FastAPI routes stay thin and only
delegate to `IngestionService` / read projections.

## Sequence

1. Ingest validates bytes, stores blob, creates shipment/document/version/run
2. Commit ingestion transaction (idempotency recorded)
3. Pipeline starts (`pipeline_started`) with `trace_id` + `run_id`
4. Document processing + extraction (`extraction_completed`)
5. Validation with Part 1 default presence rules (`validation_completed`)
6. Routing / decision (`decision_completed`)
7. Document → `decided`; run → `succeeded` (or fail-closed paths)

## State transitions

| Entity | Path |
|--------|------|
| Document | `content_available → in_pipeline → extracted → validated → decided` |
| Document (failure) | any mid-state → `failed` |
| Verification run | `queued → running → succeeded \| failed` |
| Shipment | `open → extracting → validating → routing → decided` |

Invalid transitions raise `InvalidLifecycleTransition` (HTTP 409).

Wire statuses: `ACCEPTED`, `PROCESSING`, `EXTRACTED`, `VALIDATED`, `DECIDED`, `FAILED`.

## Failure handling

| Stage failure | Behavior |
|---------------|----------|
| Extractor | Persist FAILED extraction; no fabricated ValidationResult; no AUTO_APPROVE |
| Validator | Fail-closed checks / FAILED status; Router cannot AUTO_APPROVE |
| Router | Controlled failure; no success decision pretends completion |
| LLM timeout / malformed | Bounded retries then fail-closed |
| Database | Controlled error; no false success response |

Successful prior stage rows are preserved when a later stage fails
(`auto_commit` checkpoints + append-only AI tables).

## Idempotency

- Ingestion `Idempotency-Key` replay returns the prior accept response
- Pipeline re-entry for a run that already has a decision is a no-op replay
- Extractor / validation / decision uniqueness is per `verification_run_id`

## Observability

Structured events (no document bodies / secrets):

- `pipeline_started`
- `document_processed`
- `extraction_completed`
- `validation_completed`
- `decision_completed`
- `pipeline_failed`

Fields include `trace_id`, `run_id`, `document_id`, `stage`, `status`, `duration_ms`.

## Persistence

| Table | Role |
|-------|------|
| `agent_executions` / `extracted_fields` / `model_call_metadata` | Extraction audit |
| `validations` | Append-only ValidationResult JSON (unique per run) |
| `decisions` | Append-only DecisionResult (failsafe cannot AUTO_APPROVE) |

## Retry behavior

- LLM transient errors: bounded retries (extractor max 2, validator judgment max 2)
- Schema / malformed: reject; never treat as success
- Non-retryable client/auth errors: immediate fail

## Security

- API key auth on document/shipment routes
- No secrets in logs
- Model output schema-validated before downstream use
- Safety constraints outrank LLM routing suggestions

## Part 2 extension points

Orchestrator can later accept alternate ingestion triggers (email), multiple
attachments, human approval transitions, and amendment workflows without
changing agent contracts. Do not introduce Kafka/K8s microservices prematurely.

## Related

- Agents: [`docs/agents/contracts.md`](../agents/contracts.md)
- API: [`docs/api/contracts.md`](../api/contracts.md)
- Lifecycle: [`docs/architecture/lifecycle-and-idempotency.md`](../architecture/lifecycle-and-idempotency.md)
