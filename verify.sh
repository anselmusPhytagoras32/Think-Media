#!/usr/bin/env bash
# Conservative test gate for an unknown React/FastAPI monorepo.
# Adapt this once you know your actual directories and test commands.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
ran=0

# React app: root/frontend/client/web, whichever exists.
for path in frontend client web .; do
  if [ -f "$path/package.json" ]; then
    if node -e "const p=require('./$path/package.json'); process.exit(p.scripts?.build ? 0 : 1)" >/dev/null 2>&1; then
      echo "== React build ($path) =="
      (cd "$path" && npm run build)
      ran=1
    fi
    if node -e "const p=require('./$path/package.json'); process.exit(p.scripts?.['test:ci'] ? 0 : 1)" >/dev/null 2>&1; then
      echo "== Frontend test:ci ($path) =="
      (cd "$path" && npm run test:ci)
      ran=1
    fi
    break
  fi
done

# Backend: only run pytest when the repo contains Python test files.
if find . -path './.venv' -prune -o -path './.orchestrator' -prune -o -path './node_modules' -prune -o -name 'test_*.py' -print | grep -q .; then
  echo '== Python pytest =='
  python3 -m pytest -q
  ran=1
fi

if [ "$ran" -eq 0 ]; then
  echo 'No build or tests detected. Add a backend test suite and/or frontend build command before approval.' >&2
  exit 1
fi
