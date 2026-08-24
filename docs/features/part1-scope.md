# Part 1 feature scope

Part 1 delivers an end-to-end **single-document** verification path suitable for demo and evaluation. Implementation occurs in later roadmap phases; this document is the scope contract.

## Must include

| Area | Detail |
|------|--------|
| Document input | Accept invoice / Bill of Lading (or equivalent trade docs) into the pipeline |
| Required extraction fields | Documented field set per supported type (finalized in agent/feature specs during implementation) |
| Confidence | Per-field confidence |
| Evidence | Per-field grounding |
| Validation | Customer-specific rules |
| Results | MATCH / MISMATCH / UNCERTAIN |
| Router | AUTO_APPROVE / HUMAN_REVIEW / AMENDMENT_REQUEST |
| Persistence | Shipment, document, validation, decision |
| Query | Including natural-language query over persisted data |
| UI | Minimal B2B operations UI |
| Samples | Clean sample + messy sample |
| Evaluation | Recorded results on samples |
| Observability | Structured logs / run correlation |
| Failure handling | Timeouts, extraction/validation failures, safe routing defaults |
| Documentation | Technical docs matching behavior |
| Demo/submission | Reproducible Part 1 demonstration |

## Must preserve (not build fully)

Extension points for Part 2: email/file triggers, multi-doc shipments, cross-doc validation, draft replies, human approval, outbound send. See `docs/architecture/part2-extension-points.md`.

## Explicit exclusions

Part 2 product features listed in `docs/requirements/scope-boundaries.md`.
