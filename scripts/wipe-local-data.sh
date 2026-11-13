#!/usr/bin/env bash
# FR01-12/NFR02/03/07: preview or reset this local workspace; never seed data.
set +x
set -euo pipefail
project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root/backend"
if [[ "${1:-}" != '--help' && "${1:-}" != '-h' ]]; then
  runtime_env="${THINKMEDIA_LOCAL_ENV:-$HOME/.local/share/thinkmedia/local.env}"
  if [[ ! -f "$runtime_env" ]]; then
    echo 'Missing local runtime configuration. Set THINKMEDIA_LOCAL_ENV.' >&2
    exit 1
  fi
  source "$runtime_env"
  # Use the same target precedence as the presentation launcher.
  if [[ -f .env.local ]]; then
    set -a
    source <(sed 's/\r$//' .env.local)
    set +a
  fi
fi
exec .venv/bin/python -m ops.wipe_local_data "$@"
