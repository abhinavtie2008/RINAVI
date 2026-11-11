#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== backend =="
cd backend
if [ ! -d .venv ]; then
  echo "missing backend/.venv — run scripts/bootstrap.sh"
  exit 1
fi
source .venv/Scripts/activate
ruff check app tests
pyright
pytest -q
cd ..

echo "== web =="
cd apps/web
npm run lint
npx tsc --noEmit
npm run test -- --run
cd ..

echo "All checks passed."
