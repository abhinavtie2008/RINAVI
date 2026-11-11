#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

(cd backend && source .venv/Scripts/activate && exec python -m uvicorn app.main:app --reload --port 8000) &
(cd apps/web && exec npm run dev) &

trap 'kill 0' EXIT
wait
