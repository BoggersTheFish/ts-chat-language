"""Explicit canonical receipt fixture updater."""

from __future__ import annotations

import argparse, json
from pathlib import Path
from .session import VerticalSliceSession

CASES={"accept":"Alice is older than Bob. Bob is older than Carol. Who is oldest?","repair":"Alice gave Sarah her key. Who owns the key?","reject":"Alice is an artist. Artists can become wealthy. Is Alice wealthy?"}

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument("--update",action="store_true");p.add_argument("--dir",default="tests/fixtures/vertical_slice");a=p.parse_args(argv);root=Path(a.dir)
    if not a.update: p.error("fixture writes require --update")
    root.mkdir(parents=True,exist_ok=True)
    for name,text in CASES.items():
        receipt=VerticalSliceSession("/tmp/ts_vertical_slice_fixture_turns").handle(text,save=False)
        (root/f"{name}.json").write_text(json.dumps(receipt.to_dict(),indent=2,sort_keys=True)+"\n")
    return 0
if __name__=="__main__": raise SystemExit(main())
