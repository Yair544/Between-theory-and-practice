#!/usr/bin/env bash
# ============================================================================
#  IncidentIQ - one-click launcher for macOS and Linux.
#    chmod +x run.sh    (once)
#    ./run.sh
#  Creates a virtual environment on first run, installs dependencies, starts
#  the server and opens a browser.
# ============================================================================

set -euo pipefail
cd "$(dirname "$0")"

echo
echo " IncidentIQ - starting up"
echo " ------------------------"

if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo
  echo " Python 3.10 or newer was not found."
  echo " Install it from https://www.python.org/downloads/ and run this again."
  exit 1
fi

FRESH=0
if [ ! -x ".venv/bin/python" ]; then
  echo " Creating a virtual environment (first run only)..."
  "$PY" -m venv .venv
  FRESH=1
fi

VENV_PY=".venv/bin/python"

if [ "$FRESH" -eq 1 ]; then
  echo " Installing dependencies (this takes a minute the first time)..."
  "$VENV_PY" -m pip install --upgrade pip --quiet --disable-pip-version-check
  "$VENV_PY" -m pip install -r requirements.txt --quiet --disable-pip-version-check
elif ! "$VENV_PY" -c "import fastapi, uvicorn" >/dev/null 2>&1; then
  echo " Installing missing dependencies..."
  "$VENV_PY" -m pip install -r requirements.txt --quiet --disable-pip-version-check
fi

exec "$VENV_PY" run.py
