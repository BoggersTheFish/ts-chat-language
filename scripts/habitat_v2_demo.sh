#!/usr/bin/env bash
set -euo pipefail
PYTHON="${PYTHON:-.venv/bin/python}"
[[ -x "$PYTHON" ]] || { echo "Run ./scripts/run_vertical_slice.sh once first." >&2; exit 1; }

"$PYTHON" -m ts_vertical_slice.chat --verbose --artifact-dir artifacts/habitat_v2/demo_receipts <<'EOF'
The door is not open.
Is the door open?
/reset
The door is open.
The door is not open.
Is the door open?
/reset
Alice owns the red key.
Alice gives the red key to Sarah.
Who owns the red key?
/reset
The key is inside the box.
The box is in the kitchen.
Where is the key?
/reset
If the door opens, the sensor activates. If the sensor activates and the system is armed, the alarm activates. The door opens. The system is armed. Is the alarm active?
/reset
Alice is in the hall.
The box is in the kitchen.
The red key is inside the box.
The north door is locked.
The red key unlocks the north door.
How can Alice open the north door?
/reset
Alice is in the hall.
The north door is locked.
How can Alice open the north door?
/quit
EOF
