#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== backend =="
cd backend
# macOS and some Linux distributions ship only python3.
if command -v python >/dev/null 2>&1; then
  PYTHON=python
else
  PYTHON=python3
fi
"$PYTHON" -m venv .venv
# shellcheck source=scripts/venv.sh
source ../scripts/venv.sh
activate_backend_venv .venv
"$PYTHON" -m pip install --upgrade pip
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
