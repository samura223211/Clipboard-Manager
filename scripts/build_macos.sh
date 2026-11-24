#!/usr/bin/env bash
# macOS: створює dist/macos/Clipboard Manager.app.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
else
  PY="python3"
  echo "Uvaha: venv not found, using system Python."
fi

exec "$PY" scripts/build_app.py "$@"
