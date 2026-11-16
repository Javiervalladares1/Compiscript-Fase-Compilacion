#!/usr/bin/env bash
# Ejecutar desde cualquier carpeta; conserva el espacio final del nombre del proyecto.
set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
fi
if ! .venv/bin/python -c 'import flask, antlr4' >/dev/null 2>&1; then
  .venv/bin/python -m pip install -r requirements.txt
fi

exec .venv/bin/python ide/app.py --host 127.0.0.1 --port "${IDE_PORT:-5001}"
