#!/usr/bin/env bash
# One-time setup for the demo UI, then start it on http://localhost:8501.
#
#   bash deploy/setup.sh          # setup + run
#   bash deploy/setup.sh --setup  # install only
#
# Needs Python 3.10+ and starter_v0/.env (copy starter_v0/.env.example and fill keys).
set -euo pipefail

cd "$(dirname "$0")/.."   # starter_v0/

if [ ! -f .env ]; then
  echo "Missing starter_v0/.env — copying .env.example. Fill in your keys, then re-run." >&2
  cp .env.example .env
  exit 1
fi

if [ ! -d .venv ]; then
  python -m venv .venv
fi

# Windows (Git Bash) keeps binaries in .venv/Scripts, Linux/macOS in .venv/bin.
if [ -x .venv/bin/python ]; then
  PY=.venv/bin/python
else
  PY=.venv/Scripts/python.exe
fi

"$PY" -m pip install --upgrade pip
"$PY" -m pip install -r requirements-streamlit.txt

if [ "${1:-}" = "--setup" ]; then
  echo "Installed. Start later with: bash deploy/setup.sh"
  exit 0
fi

"$PY" -m streamlit run app.py --server.port 8501
