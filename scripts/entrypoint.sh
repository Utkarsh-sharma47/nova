#!/usr/bin/env sh
# Container entrypoint: migrate, then exec the API (PID 1 for signals).
set -eu

echo "nova-entrypoint: waiting for database then applying migrations"

python - <<'PY'
import os
import sys
import time

from sqlalchemy import create_engine, text

url = os.environ.get("DATABASE_URL")
if not url:
    print("DATABASE_URL is required", file=sys.stderr)
    sys.exit(1)

timeout = float(os.environ.get("DATABASE_CONNECT_TIMEOUT_SECONDS", "5"))
deadline = time.time() + float(os.environ.get("DB_WAIT_SECONDS", "60"))
last_error = None

while time.time() < deadline:
    engine = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": int(timeout)})
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        print("nova-entrypoint: database is ready")
        break
    except Exception as exc:  # noqa: BLE001
        last_error = exc
        engine.dispose()
        time.sleep(1)
else:
    print(f"nova-entrypoint: database not ready: {last_error}", file=sys.stderr)
    sys.exit(1)
PY

alembic upgrade head
echo "nova-entrypoint: migrations applied"

# exec replaces shell so uvicorn receives SIGTERM for clean shutdown
exec "$@"
