#!/usr/bin/env bash
set -euo pipefail

mkdir -p artifacts/vertical_slice_demo
script --quiet --return --log-timing artifacts/vertical_slice_demo/two_minute_demo.timing \
  --command "./scripts/two_minute_demo.sh" \
  artifacts/vertical_slice_demo/two_minute_demo.typescript
echo "Recorded continuous session: artifacts/vertical_slice_demo/two_minute_demo.typescript"
