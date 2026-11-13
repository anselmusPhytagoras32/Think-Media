#!/usr/bin/env bash
# FR01–11 / NFR06: repeatable existing WSL presentation runtime.
set -euo pipefail
cd "$(dirname "$0")/../backend"
runtime_env="${THINKMEDIA_LOCAL_ENV:-$HOME/.local/share/thinkmedia/local.env}"
if [[ ! -f "$runtime_env" ]]; then
  echo "Missing private local environment. See docs/LOCAL_DEMO.md." >&2
  exit 1
fi
source "$runtime_env"
if [[ "${1:-}" == "--browser-tests" ]]; then
  source "$HOME/.local/share/thinkmedia/browser-demo/browser.env"
  # Repeated synthetic browser runs must not consume presentation auth quotas.
  # This setting is limited to the separate disposable browser database/API.
  export APP_REGISTER_MAX_ATTEMPTS=1000
  # FR10/NFR02: browser QA must never use a presentation provider credential.
  export APP_ASSISTANT_MODE=retrieval APP_ASSISTANT_API_KEY='' APP_ASSISTANT_CALL_BUDGET=0
  port=8001
else
  # FR10/NFR02: override launcher defaults with the private backend dotenv file.
  # Normalize Windows line endings; dotenv values must use shell-safe quoting.
  if [[ -f .env.local ]]; then
    set -a
    source <(sed 's/\r$//' .env.local)
    set +a
  fi
  port=8000
fi
pg_data="$HOME/.local/share/thinkmedia/pgdata"
if ! "$PG_BIN/pg_ctl" -D "$pg_data" status >/dev/null 2>&1; then
  "$PG_BIN/pg_ctl" -D "$pg_data" -l "$HOME/.local/share/thinkmedia/postgres.log" \
    -o "-h 127.0.0.1 -p 55432 -k $HOME/.local/share/thinkmedia/socket" start
fi
.venv/bin/python -m alembic upgrade head
exec .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port "$port"
