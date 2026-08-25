#!/bin/sh
set -eu

HTML_ROOT="${NOVA_HTML_ROOT:-/usr/share/nginx/html}"
CONFIG_PATH="${HTML_ROOT}/runtime-config.js"

TOKEN_JSON=$(API_AUTH_TOKEN="${API_AUTH_TOKEN:-}" python3 - <<'PY'
import json
import os
print(json.dumps(os.environ.get("API_AUTH_TOKEN", "")))
PY
)

BASE_JSON=$(VITE_API_BASE_URL="${VITE_API_BASE_URL:-}" python3 - <<'PY'
import json
import os
print(json.dumps(os.environ.get("VITE_API_BASE_URL", "")))
PY
)

cat > "${CONFIG_PATH}" <<EOF
/* Generated at container start — not baked into the image build. */
window.__NOVA_RUNTIME__ = {
  apiBaseUrl: ${BASE_JSON},
  apiAuthToken: ${TOKEN_JSON}
};
EOF

chmod 644 "${CONFIG_PATH}"
exec "$@"
