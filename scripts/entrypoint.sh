#!/usr/bin/env sh
set -eu

echo "nova-entrypoint: waiting for database"
python - <<'PY'
import os
import sys
import time

from sqlalchemy import create_engine, text

url = os.environ.get("DATABASE_URL")
if not url:
    print("nova-entrypoint: DATABASE_URL is required", file=sys.stderr)
    raise SystemExit(1)

connect_timeout = int(os.environ.get("DATABASE_CONNECT_TIMEOUT_SECONDS", "5"))
deadline = time.monotonic() + float(os.environ.get("DB_WAIT_SECONDS", "60"))

while time.monotonic() < deadline:
    engine = create_engine(
        url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": connect_timeout},
    )
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        engine.dispose()
        print("nova-entrypoint: database is ready")
        break
    except Exception:
        engine.dispose()
        time.sleep(1)
else:
    print("nova-entrypoint: database unavailable before timeout", file=sys.stderr)
    raise SystemExit(1)
PY

alembic upgrade head
echo "nova-entrypoint: migrations applied"
exec "$@"
