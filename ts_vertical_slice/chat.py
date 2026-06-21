"""CLI for the bounded verifier-first vertical slice."""

from __future__ import annotations

import argparse, json
from .session import VerticalSliceSession
from .agent_session import HabitatV3Session

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
    parser.add_argument("--verbose",action="store_true"); parser.add_argument("--prompt"); parser.add_argument("--artifact-dir",default="artifacts/turns");parser.add_argument("--habitat-v3",action="store_true")
    args=parser.parse_args(argv); session=VerticalSliceSession(args.artifact_dir); mode=args.verbose
    if args.habitat_v3:return agent_main(args)
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


def agent_main(args):
    session=HabitatV3Session(args.artifact_dir);print("TS Habitat v3 — deterministic verifier-first agent. Type /help.")
    def emit(receipt):
        print(f"[{receipt['decision']['status']}: {receipt['decision']['subtype']}] {receipt['rendering']['text']}");print(f"Receipt: {session.last_path}")
        if args.verbose:print(json.dumps(receipt,indent=2,sort_keys=True))
    if args.prompt:emit(session.handle(args.prompt));return 0
    while True:
        try:line=input("> ").strip()
        except (EOFError,KeyboardInterrupt):print();break
        if not line:continue
        if line in {"/quit","/exit"}:break
        if line=="/help":print("World: /world /state /facts /conflicts /cluster /topology /connections /agents\nGoals: /goals /goal <id> /add-goal <goal> /pause-goal <id> /resume-goal <id> /abandon-goal <id>\nAgent: /run [steps] /step /stop /plan /replan\nTension: /tension [id]\nReflection: /reflections /reflection <id> /lessons /lesson <id> /approve-lesson <id> /reject-lesson <id>\nEvents/replay: /events /schedule-event <event> /inject-event <event> /receipt /trace /replay /export-run /reset");continue
        parts=line.split(maxsplit=1);cmd=parts[0];arg=parts[1] if len(parts)>1 else ""
        if cmd=="/run":emit(session.run(int(arg) if arg else None));continue
        if cmd=="/step":emit(session.step());continue
        if cmd=="/stop":session.loop.stop();print("Stop requested.");continue
        if cmd=="/replan":session.replan();print("Current plan invalidated for verified replanning.");continue
        if cmd=="/reset":print(session.reset());continue
        if cmd in {"/add-goal","/schedule-event","/inject-event"}:emit(session.handle(arg));continue
        if cmd in {"/pause-goal","/resume-goal","/abandon-goal"}:
            goal=session.goals.goals[arg];from ts_reasoner.agent_control import GoalStatus
            target={"/pause-goal":GoalStatus.PAUSED,"/resume-goal":GoalStatus.ACTIVE,"/abandon-goal":GoalStatus.ABANDONED}[cmd];print(json.dumps(session.goals.transition(goal.goal_id,target,turn=session.turn).__dict__,indent=2));continue
        if cmd=="/approve-lesson":print(json.dumps(session.approve_lesson(arg),indent=2));continue
        if cmd=="/reject-lesson":print(json.dumps(session.reject_lesson(arg),indent=2));continue
        if cmd in {"/world","/state"}:print(json.dumps({"hash":session.loop.world.hash,"signed":{k:v.__dict__ for k,v in session.loop.world.signed_state.items()}},indent=2,sort_keys=True));continue
        if cmd=="/facts":print(json.dumps({k:v.__dict__ for k,v in session.loop.world.facts.items()},indent=2,sort_keys=True));continue
        if cmd=="/conflicts":print(json.dumps([k for k,v in session.loop.world.signed_state.items() if v.status=="CONFLICTED"],indent=2));continue
        if cmd in {"/topology","/connections"}:print(json.dumps(session.loop.world.topology.to_dict(),indent=2,sort_keys=True));continue
        if cmd=="/agents":print(json.dumps({k:v.__dict__ for k,v in session.loop.world.agents.items()},indent=2,sort_keys=True));continue
        if cmd=="/goals":print(json.dumps(session.goals.to_dict(),indent=2,sort_keys=True));continue
        if cmd=="/goal":print(json.dumps(session.goals.goals[arg].to_dict(),indent=2,sort_keys=True));continue
        if cmd=="/cluster":print(json.dumps(next((x for x in reversed(session.loop.run.loop_steps) if x['phase']=='ACTIVATE_CLUSTER'),{}),indent=2,sort_keys=True));continue
        if cmd=="/plan":print(json.dumps(session.loop.current_plan.__dict__ if session.loop.current_plan else {},indent=2,sort_keys=True,default=lambda x:x.__dict__));continue
        if cmd=="/tension":
            data=session.loop.tension.to_dict();print(json.dumps(data.get(arg,data) if arg else data,indent=2,sort_keys=True));continue
        if cmd=="/events":print(json.dumps([x.__dict__ for x in session.environment.snapshot().scheduled_events],indent=2,sort_keys=True,default=lambda x:x.__dict__));continue
        if cmd=="/reflections":print(json.dumps([x.__dict__ for x in session.loop.run.reflections],indent=2,sort_keys=True));continue
        if cmd=="/reflection":print(json.dumps(next(x.__dict__ for x in session.loop.run.reflections if x.reflection_id==arg),indent=2,sort_keys=True));continue
        if cmd=="/lessons":print(json.dumps({k:v.__dict__ for k,v in session.loop.run.lessons.items()},indent=2,sort_keys=True));continue
        if cmd=="/lesson":print(json.dumps(session.loop.run.lessons[arg].__dict__,indent=2,sort_keys=True));continue
        if cmd in {"/receipt","/trace"}:print(json.dumps(session.receipts[-1] if session.receipts else {},indent=2,sort_keys=True));continue
        if cmd=="/replay":print(session.loop.run.final_replay_hash);continue
        if cmd=="/export-run":
            path=session.artifact_dir/"exported_run.json";path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(session.receipts[-1],indent=2,sort_keys=True)+"\n");print(path);continue
        emit(session.handle(line))
    return 0

if __name__=="__main__": raise SystemExit(main())
