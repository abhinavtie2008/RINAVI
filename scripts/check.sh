#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== backend =="
cd backend
# shellcheck source=scripts/venv.sh
source ../scripts/venv.sh
activate_backend_venv .venv
ruff check app tests
python -m pyright
python -m pytest -q
cd ..

echo "== web =="
cd apps/web
npm run lint
npx next typegen
npx tsc --noEmit
npm run test -- --run
npm run build
cd ..

echo "== demo (docs/) =="
node scripts/check_demo_sync.mjs

echo "All checks passed."
