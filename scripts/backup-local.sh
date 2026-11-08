#!/usr/bin/env bash
# NFR07: private local dump and restore into a fresh database, never overwrite.
set -euo pipefail
cd "$(dirname "$0")/../backend"
source "${THINKMEDIA_LOCAL_ENV:-$HOME/.local/share/thinkmedia/local.env}"
pg_data="$HOME/.local/share/thinkmedia/pgdata"
if ! "$PG_BIN/pg_ctl" -D "$pg_data" status >/dev/null 2>&1; then
  "$PG_BIN/pg_ctl" -D "$pg_data" -l "$HOME/.local/share/thinkmedia/postgres.log" \
    -o "-h 127.0.0.1 -p 55432 -k $HOME/.local/share/thinkmedia/socket" start
fi
export DATABASE_URL="${LOCAL_BACKUP_DATABASE_URL:?Configure the separate local backup role.}"
backup_root="$HOME/.local/share/thinkmedia/backups"
umask 077
restore_args=(--restore-smoke)
if [[ "${1:-}" == "--dump-only" ]]; then
  restore_args=()
elif [[ -n "${1:-}" ]]; then
  echo 'Usage: backup-local.sh [--dump-only]' >&2
  exit 1
fi
.venv/bin/python -m ops.backup --pg-bin "$PG_BIN" \
  --output "$backup_root/presentation-$(date -u +%Y%m%dT%H%M%SZ)-$$.dump" "${restore_args[@]}"
