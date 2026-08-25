# GoComet compliance delta (post-implementation)

| Field | Value |
|-------|-------|
| Date | 2026-08-25 |
| Branch | `feature/final-gocomet-compliance` |
| Basis | Closes P0/P1 gaps from [gocomet-final-rubric-audit.md](./gocomet-final-rubric-audit.md) |

## P0 closed

| Gap | Implementation | Test / evidence |
|-----|----------------|-----------------|
| GoComet PRD | `docs/submission/prd.md` | Doc review |
| Assignment fields | `src/nova/extraction/fields.py` + heuristic aliases | `tests/extraction/test_assignment_fields.py`, extractor eval |
| Images + vision path | `RasterImageAdapter`, `LLMImagePart`, OpenAI adapter | `tests/documents/test_raster_image.py`, `tests/llm/test_openai_compatible.py`, API PNG accept |
| D3 write-up + diagram | `docs/submission/technical-writeup.md`, `architecture-diagram.md` | Doc review |
| Real document UI | `GET .../content` + `DocumentPreview` | API content test, DocumentPage Vitest |

## P1 closed

| Gap | Implementation |
|-----|----------------|
| Flagged this week | Query classifier + `time_range` filter |
| Extractor golden eval | `src/nova/evaluation/extractor/` |
| Stale agents README | Fixed |
| Provider config docs | `.env.example`, supported-types, README |

## Remaining limitations (honest)

- Live vision quality/cost not measured without real API keys
- Scanned-PDF dedicated OCR adapter still deferred (PNG/JPEG vision path covers assignment image MUST)
- Customer rule authoring UI still thin (defaults + request rules)
- Remote production deploy still NOT EXECUTED

Do not claim “complete” beyond what tests and demo prove on MockLLM + optional live provider.
