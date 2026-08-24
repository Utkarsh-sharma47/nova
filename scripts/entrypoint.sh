#!/bin/sh
set -eu

echo "Running alembic upgrade head..."
alembic upgrade head

echo "Starting Nova API..."
exec uvicorn nova.api.main:create_app --factory --host 0.0.0.0 --port 8000
