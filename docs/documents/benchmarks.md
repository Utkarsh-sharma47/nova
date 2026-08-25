# Document processing benchmarks

Lightweight specification — not a premature optimization program.

## Metrics

| Metric | How |
|--------|-----|
| Processing latency | `DocumentProcessingResult.duration_ms` / wall clock |
| Document size vs time | Vary page count / byte size; record pairs |
| Memory | Optional RSS delta via `/proc/self/status` in benchmark script |

## Commands

```bash
python scripts/benchmark_document_processing.py
pytest -q tests/documents/test_large_file.py
```

## Baseline expectations (dev laptop / CI)

| Workload | Soft ceiling |
|----------|--------------|
| Small text invoice | < 1 s |
| 1–5 page synthetic PDF | < 5 s |

Baselines are recorded by the script when run; they are informational, not CI gates beyond smoke ceilings.
