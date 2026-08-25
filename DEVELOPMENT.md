# Development

Local development guidance for Nova.

## Current status

**Phase 3 document processing:** `nova.documents` implements ADR-0006
(`DocumentProcessorPort`, intake validation, digital PDF + text adapters,
local blob store). FastAPI ingestion API, Extractor/Validator/Router agents,
and UI are **not** implemented on this branch.

## Prerequisites

- Python **3.12+**
- Docker (optional, for Compose Postgres skeleton)
- Node **20+** (Phase 6 UI only)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

## Local checks

```bash
./scripts/check-docs-structure.sh
./scripts/check-secret-patterns.sh
ruff check src tests
mypy
pytest -q
python scripts/benchmark_document_processing.py
```

## Repository layout (document processing)

```text
.
├── src/nova/contracts/     # Phase 2 Pydantic domain contracts
├── src/nova/documents/     # DocumentProcessorPort + adapters
├── tests/contracts/        # Schema tests
├── tests/documents/        # Processor / security / storage tests
├── docs/documents/         # Supported types, pipeline, adapters, security
├── scripts/benchmark_document_processing.py
├── docs/                   # Architecture, ADRs, requirements
├── Dockerfile              # Phase 2 skeleton (import smoke)
├── docker-compose.yml      # Postgres + API placeholder
├── pyproject.toml
└── scripts/
```

## Branching

Follow [`docs/operations/git-workflow.md`](docs/operations/git-workflow.md):

- Branch from latest `main`
- Prefixes: `feature/`, `fix/`, `docs/`, `test/`, `chore/`
- Never push directly to `main`

## Environment configuration

Use `.env.example` as a template. Never commit secrets. See [`docs/security/baseline.md`](docs/security/baseline.md).

## Related documents

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [TESTING.md](TESTING.md)
- [docs/documents/](docs/documents/)
- [docs/architecture/document-processing.md](docs/architecture/document-processing.md)
- [docs/architecture/technology-stack.md](docs/architecture/technology-stack.md)
