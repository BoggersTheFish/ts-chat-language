#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${TS_REASONER_PATH:-$ROOT/../TS-Reasoner-v0}:$ROOT${PYTHONPATH:+:$PYTHONPATH}"
cd "$ROOT"
python3 scripts/habitat_v3_demo.py
