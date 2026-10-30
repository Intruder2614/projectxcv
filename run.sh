#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then echo "Python 3 is required. Install Python 3.10+ first."; exit 1; fi
if [ ! -d .venv ]; then python3 -m venv .venv; fi
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
exec uvicorn app:app --host "${HOST:-127.0.0.1}" --port "${PORT:-8000}"
