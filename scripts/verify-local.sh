#!/usr/bin/env bash
# FR01–12 / NFR01–11: verification uses a separate disposable database.
set -euo pipefail
cd "$(dirname "$0")/.."
runtime_env="${THINKMEDIA_LOCAL_ENV:-$HOME/.local/share/thinkmedia/local.env}"
if [[ ! -f "$runtime_env" ]]; then
  echo "Set THINKMEDIA_LOCAL_ENV to your private local runtime configuration." >&2
  exit 1
fi
source "$runtime_env"
if [[ -z "${TEST_DATABASE_URL:-}" ]]; then
  echo "Set TEST_DATABASE_URL to a separate disposable test database." >&2
  exit 1
fi
backend/.venv/bin/python - <<'PY'
import os
from sqlalchemy.engine import make_url
test = make_url(os.environ['TEST_DATABASE_URL'])
live = make_url(os.environ.get('DATABASE_URL', 'postgresql://localhost/presentation'))
if (test.get_backend_name() != 'postgresql'
        or test.host not in {'localhost', '127.0.0.1', '::1'}
        or test.query or not (test.database or '').endswith('_test')
        or test.database == live.database):
    raise SystemExit('Use a separate loopback PostgreSQL database ending in _test; presentation data must never be a test target.')
PY
if ! "$PG_BIN/pg_ctl" -D "$HOME/.local/share/thinkmedia/pgdata" status >/dev/null 2>&1; then
  "$PG_BIN/pg_ctl" -D "$HOME/.local/share/thinkmedia/pgdata" \
    -l "$HOME/.local/share/thinkmedia/postgres.log" \
    -o "-h 127.0.0.1 -p 55432 -k $HOME/.local/share/thinkmedia/socket" start
fi
cd backend
.venv/bin/python -m pytest -q
DATABASE_URL="$TEST_DATABASE_URL" .venv/bin/python -m alembic check
cd ..
backend/.venv/bin/python -m unittest evaluation.test_evaluation -v
# Frontend uses native Windows dependencies on this workstation.
# Run npm.cmd run build in frontend. For browser tests follow the explicit
# isolated API8001/frontend5174 setup in docs/PRESENTATION_READINESS.md.
