"""CLI for the bounded verifier-first vertical slice."""

from __future__ import annotations

import argparse, json
from .session import VerticalSliceSession

BANNER="TS Chat — verifier-first vertical slice\nBounded deterministic language and reasoning demo.\nType /help for supported examples."
EXAMPLES=["Alice is older than Bob. Bob is older than Carol. Who is oldest?","The red key opens the north door. Which door does the red key open?","The alarm activates if the door is open and the system is armed. The door is open. The system is armed. Is the alarm active?","Alice gave Sarah her key. Who owns the key?","I must verify the backup before deleting the repository. What should happen first?"]

def verbose(receipt):
    d=receipt.to_dict()
    for title,key in (("INPUT","input_text"),("PARSE","parse_status"),("MEANING GRAPH","meaning_graph"),("BRIDGE","reasoning_request"),("VERIFIER CHECKS","verifier_checks"),("REPAIR","repair_result"),("FINAL DECISION","final_status"),("RESPONSE","final_response"),("REPLAY HASH","deterministic_replay_hash")):
        value=d[key]; print(f"\n{title}\n"+ (json.dumps(value,indent=2,sort_keys=True) if isinstance(value,(dict,list,tuple)) else str(value)))

def emit(session, text, is_verbose):
    receipt=session.handle(text); print(f"[{receipt.final_status}] {receipt.final_response}"); print(f"Receipt: {session.last_path}")
    if is_verbose: verbose(receipt)

def main(argv=None):
    parser=argparse.ArgumentParser(description="Bounded deterministic TS language-to-verifier demo")
    parser.add_argument("--verbose",action="store_true"); parser.add_argument("--prompt"); parser.add_argument("--artifact-dir",default="artifacts/turns")
    args=parser.parse_args(argv); session=VerticalSliceSession(args.artifact_dir); mode=args.verbose
    print(BANNER)
    if args.prompt: emit(session,args.prompt,mode); return 0
    while True:
        try: line=input("> ").strip()
        except (EOFError,KeyboardInterrupt): print(); break
        if not line: continue
        if line=="/quit": break
        if line=="/help": print("Supported: relational facts/queries, older-than ordering, Boolean conjunctions, ambiguity clarification, and before/after planning."); continue
        if line=="/examples": print("\n".join(f"- {x}" for x in EXAMPLES)); continue
        if line=="/receipt": print(json.dumps(session.last_receipt.to_dict(),indent=2,sort_keys=True) if session.last_receipt else "No receipt yet."); continue
        if line=="/verbose": mode=True; print("Verbose mode enabled."); continue
        if line=="/compact": mode=False; print("Compact mode enabled."); continue
        if line=="/reset": print(f"State reset: {session.reset()}"); continue
        emit(session,line,mode)
    return 0

if __name__=="__main__": raise SystemExit(main())
