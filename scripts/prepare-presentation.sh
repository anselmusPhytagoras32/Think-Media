#!/usr/bin/env bash
# FR01/02/11: explicitly provision dedicated local synthetic role accounts.
set -euo pipefail
cd "$(dirname "$0")/../backend"
source "${THINKMEDIA_LOCAL_ENV:-$HOME/.local/share/thinkmedia/local.env}"
.venv/bin/python -m ops.presentation_accounts
