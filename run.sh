#!/usr/bin/env bash
# Run the API using the project virtualenv (avoids missing dependencies).
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "Creating virtualenv..."
  python3.12 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi

exec .venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload "$@"
