#!/usr/bin/env bash
# Sourced by the other scripts; not meant to be executed directly.
#
# A virtualenv lays its activation script out differently per platform:
# Windows puts it in Scripts/, everywhere else in bin/. Hardcoding Scripts/
# made bootstrap, dev and check unusable on macOS and Linux.

activate_backend_venv() {
  local venv_dir="${1:-backend/.venv}"
  if [ -f "$venv_dir/Scripts/activate" ]; then
    # shellcheck disable=SC1091
    . "$venv_dir/Scripts/activate"
  elif [ -f "$venv_dir/bin/activate" ]; then
    # shellcheck disable=SC1091
    . "$venv_dir/bin/activate"
  else
    echo "missing $venv_dir — run scripts/bootstrap.sh" >&2
    return 1
  fi
}
