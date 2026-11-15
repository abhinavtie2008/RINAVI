#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

(
  cd backend
  # shellcheck source=scripts/venv.sh
  source ../scripts/venv.sh
  activate_backend_venv .venv
  RINAVI_ENVIRONMENT=development exec python -m uvicorn app.main:app --reload --port 8000
) &
(cd apps/web && exec npm run dev) &

trap 'kill 0' EXIT
wait
