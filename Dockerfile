# Phase 2 skeleton — no application business logic.
# Build context expects Python contracts package only for now.

FROM python:3.12-slim AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --upgrade pip && pip install .

# Placeholder: Phase 3+ will start uvicorn for FastAPI.
CMD ["python", "-c", "import nova; print('nova', nova.__version__)"]
