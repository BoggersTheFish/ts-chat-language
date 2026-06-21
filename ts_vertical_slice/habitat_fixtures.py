"""Explicit Habitat v2 receipt fixture updater; never called by normal tests."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from .session import VerticalSliceSession

CASES={
 "signed_false":["The door is not open.","Is the door open?"],
 "conflicted":["The door is open.","The door is not open.","Is the door open?"],
 "ownership_transfer":["Alice owns the red key.","Alice gives the red key to Sarah.","Who owns the red key?"],
 "causal_chain":["If the door opens, the sensor activates. If the sensor activates and the system is armed, the alarm activates. The door opens. The system is armed. Is the alarm active?"],
 "verified_plan":["Alice is in the hall.","The box is in the kitchen.","The red key is inside the box.","The north door is locked.","The red key unlocks the north door.","How can Alice open the north door?"],
}
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument("--update",action="store_true");p.add_argument("--dir",default="tests/fixtures/habitat_v2");a=p.parse_args(argv)
 if not a.update:p.error("fixture writes require --update")
 root=Path(a.dir);root.mkdir(parents=True,exist_ok=True)
 for name,turns in CASES.items():
  session=VerticalSliceSession("/tmp/habitat_v2_fixture_turns")
  for text in turns:receipt=session.handle(text,save=False)
  (root/f"{name}.json").write_text(json.dumps(receipt.to_dict(),indent=2,sort_keys=True)+"\n")
 return 0
if __name__=="__main__":raise SystemExit(main())
