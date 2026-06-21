"""CLI for the bounded verifier-first vertical slice."""

from __future__ import annotations

import argparse, json
from .session import VerticalSliceSession

BANNER="TS Chat — verifier-first vertical slice\nBounded deterministic language and reasoning demo.\nType /help for supported examples."
EXAMPLES=["Alice is older than Bob. Bob is older than Carol. Who is oldest?","The red key opens the north door. Which door does the red key open?","The alarm activates if the door is open and the system is armed. The door is open. The system is armed. Is the alarm active?","Alice gave Sarah her key. Who owns the key?","I must verify the backup before deleting the repository. What should happen first?"]

def verbose(receipt):
    d=receipt.to_dict()
    for title,key in (("INPUT","input_text"),("PARSE","parse_status"),("MEANING GRAPH","meaning_graph"),("SEMANTIC MERGE","semantic_merge"),("CLUSTER ACTIVATION","cluster_activation"),("SIGNED WORLD STATE","signed_world_state"),("BRIDGE","reasoning_request"),("VERIFIER CHECKS","verifier_checks"),("EVENTS","events"),("STATE TRANSITIONS","state_transitions"),("CAUSAL DERIVATIONS","causal_derivations"),("PLANNING","planning"),("REPAIR","repair_result"),("FINAL DECISION","final_status"),("DECISION SUBTYPE","decision_subtype"),("RESPONSE","final_response"),("REPLAY HASH","deterministic_replay_hash")):
        value=d[key]; print(f"\n{title}\n"+ (json.dumps(value,indent=2,sort_keys=True) if isinstance(value,(dict,list,tuple)) else str(value)))

def emit(session, text, is_verbose):
    receipt=session.handle(text); suffix=f": {receipt.decision_subtype}" if receipt.decision_subtype else ""; print(f"[{receipt.final_status}{suffix}] {receipt.final_response}"); print(f"Receipt: {session.last_path}")
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
        if line=="/help": print("Supported: v1 relations/ordering plus Habitat signed state, ownership, containment, events, causal rules, and bounded verified plans. Commands: /world /state /facts /conflicts /cluster /plan /receipt /reset /verbose /compact /quit"); continue
        if line=="/examples": print("\n".join(f"- {x}" for x in EXAMPLES)); continue
        if line=="/receipt": print(json.dumps(session.last_receipt.to_dict(),indent=2,sort_keys=True) if session.last_receipt else "No receipt yet."); continue
        if line=="/verbose": mode=True; print("Verbose mode enabled."); continue
        if line=="/compact": mode=False; print("Compact mode enabled."); continue
        if line=="/reset": print(f"State reset: {session.reset()}"); continue
        if line=="/world": print(json.dumps(session.state.world.to_dict(),indent=2,sort_keys=True)); continue
        if line=="/state": print(json.dumps({key:item["status"] for key,item in session.state.world.to_dict().items()},indent=2,sort_keys=True)); continue
        if line=="/facts": print(json.dumps({key:item for key,item in session.state.world.to_dict().items() if item["kind"] in {"fact","event_effect"} and item["active"]},indent=2,sort_keys=True)); continue
        if line=="/conflicts": print(json.dumps(session.state.world.conflicts(),indent=2)); continue
        if line=="/cluster": print(json.dumps(session.state.world.latest_activation.to_dict(),indent=2,sort_keys=True)); continue
        if line=="/plan": print(json.dumps(session.last_receipt.planning if session.last_receipt else {},indent=2,sort_keys=True)); continue
        emit(session,line,mode)
    return 0

if __name__=="__main__": raise SystemExit(main())
