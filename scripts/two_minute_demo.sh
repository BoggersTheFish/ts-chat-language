#!/usr/bin/env bash
set -euo pipefail

PYTHON="${PYTHON:-.venv/bin/python}"
if [[ ! -x "$PYTHON" ]]; then
  echo "Missing $PYTHON. Run ./scripts/run_vertical_slice.sh --prompt '/help' once to install." >&2
  exit 1
fi

echo "=== ACCEPT (verbose evidence path) ==="
"$PYTHON" -m ts_vertical_slice.chat --verbose --artifact-dir artifacts/demo_receipts/accept --prompt "Alice is older than Bob. Bob is older than Carol. Who is oldest?"
echo
echo "=== REPAIR ==="
"$PYTHON" -m ts_vertical_slice.chat --artifact-dir artifacts/demo_receipts/repair --prompt "Alice gave Sarah her key. Who owns the key?"
echo
echo "=== REJECT ==="
"$PYTHON" -m ts_vertical_slice.chat --artifact-dir artifacts/demo_receipts/reject --prompt "Alice is an artist. Artists can become wealthy. Is Alice wealthy?"
