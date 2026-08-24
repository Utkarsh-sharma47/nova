# Production-minded API image for Nova (ADR-0008).
# Multi-stage: build deps in builder; slim runtime as non-root with healthcheck.

FROM python:3.12-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && python -m venv /opt/venv

ENV PATH="/opt/venv/bin:${PATH}"

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --upgrade pip \
    && pip install .

FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}" \
    HOME=/home/nova

RUN groupadd --system --gid 10001 nova \
    && useradd --system --uid 10001 --gid nova --create-home --home-dir /home/nova nova

COPY --from=builder /opt/venv /opt/venv
COPY --chown=nova:nova alembic.ini ./
COPY --chown=nova:nova alembic ./alembic
COPY --chown=nova:nova scripts/entrypoint.sh /entrypoint.sh

USER root
RUN chmod 755 /entrypoint.sh
USER nova

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "nova.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
