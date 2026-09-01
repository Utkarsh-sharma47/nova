# Features

Per-feature documentation for Nova.

## Feature index

| Feature | Doc | Status |
|---------|-----|--------|
| Part 1 scope contract | [part1-scope.md](./part1-scope.md) | Done (scope; implementation later) |
| Document ingestion | [document-ingestion.md](./document-ingestion.md) | Phase 3 implemented |
| Extractor agent | [extractor-agent.md](./extractor-agent.md) | Phase 4 implemented |
| End-to-end pipeline | [end-to-end-pipeline.md](./end-to-end-pipeline.md) | Phase 7 implemented |
| Query / Intelligence API | [query-intelligence-api.md](./query-intelligence-api.md) | Phase 8 implemented (adapted on Phase 7 schema) |
| Part 1 operations UI | [operations-ui.md](./operations-ui.md) | Phase 9 implemented |
| Document agreement classification | [document-agreement-classification.md](./document-agreement-classification.md) | Analytical layer over extraction + validation |

## Creating a feature doc

1. Copy [FEATURE_TEMPLATE.md](FEATURE_TEMPLATE.md).
2. Use a stable slug filename (for example `document-intake.md`).
3. Link the feature from this README and related requirements/product docs.
4. Keep the document updated when behavior changes.
5. Cite `REQ-*` IDs.

## Related

- [FEATURE_TEMPLATE.md](FEATURE_TEMPLATE.md)
- [Requirements](../requirements/)
- [Product](../product/)
- [Architecture](../architecture/)
