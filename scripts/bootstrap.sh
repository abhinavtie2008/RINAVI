#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== backend =="
cd backend
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
# Windows Application Control on this machine blocks SQLAlchemy's C extensions;
# force pure-Python mode so the editable install never re-breaks imports.
export DISABLE_SQLALCHEMY_CEXT=1
pip install -e ".[dev]"
cd ..

echo "== web =="
cd apps/web
npm install
cd ..

echo "Bootstrap complete. Run scripts/check.sh to verify."
