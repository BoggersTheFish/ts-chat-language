#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$ROOT/artifacts/habitat_v3_demo"
cd "$ROOT"
script -q -e -c "scripts/run_habitat_v3.sh" artifacts/habitat_v3_demo/habitat_v3_demo.typescript
