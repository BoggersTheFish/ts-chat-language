#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REASONER="${TS_REASONER_PATH:-$ROOT/../TS-Reasoner-v0}"
[[ -f "$REASONER/pyproject.toml" ]] || { echo "TS-Reasoner-v0 must be cloned beside ts-chat-language (or set TS_REASONER_PATH)." >&2; exit 2; }
[[ -d "$ROOT/.venv" ]] || python3 -m venv "$ROOT/.venv"
"$ROOT/.venv/bin/python" -m pip install -q -e "$REASONER" -e "$ROOT"
exec "$ROOT/.venv/bin/python" -m ts_vertical_slice.chat "$@"
