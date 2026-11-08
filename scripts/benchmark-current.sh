#!/usr/bin/env bash
# NFR01/02/03: exercise this revision with an isolated synthetic PostgreSQL fixture.
set -euo pipefail
cd "$(dirname "$0")/.."
source "${THINKMEDIA_LOCAL_ENV:-$HOME/.local/share/thinkmedia/local.env}"
export DATABASE_URL="${TEST_DATABASE_URL:?A separate disposable test database is required.}"
export APP_ENV=test APP_ASSISTANT_MODE=disabled
mkdir -p .local
backend/.venv/bin/python - <<'PY'
import os
from sqlalchemy.engine import make_url
url = make_url(os.environ['DATABASE_URL'])
if url.host not in {'localhost', '127.0.0.1', '::1'} or url.query or not (url.database or '').endswith('_test'):
    raise SystemExit('Benchmark requires a loopback disposable _test database, without query overrides.')
PY
cd backend
.venv/bin/python -m alembic upgrade head
.venv/bin/python ../scripts/seed-benchmark.py
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8002 > ../.local/benchmark-api.log 2>&1 &
benchmark_pid=$!
trap 'kill -INT "$benchmark_pid" 2>/dev/null || true; wait "$benchmark_pid" || true' EXIT
.venv/bin/python - <<'PY'
import time
import httpx
deadline = time.monotonic() + 90
with httpx.Client(trust_env=False, timeout=1) as client:
    while time.monotonic() < deadline:
        try:
            if client.get('http://127.0.0.1:8002/health').is_success:
                break
        except httpx.HTTPError:
            pass
        time.sleep(.5)
    else:
        raise SystemExit('Isolated benchmark API did not become ready.')
PY
.venv/bin/python -m ops.benchmark --base-url http://127.0.0.1:8002 \
  --concurrency 20 --requests 200 --output reports/performance-presentation.json > ../.local/benchmark-result.log
.venv/bin/python - <<'PY'
import json
from pathlib import Path
report = json.loads(Path('reports/performance-presentation.json').read_text())
print(json.dumps({key: report[key] for key in ('concurrent_users', 'measured_requests', 'p95_ms', 'failures', 'target_met', 'database_row_counts', 'dataset_kind')}, indent=2))
PY
