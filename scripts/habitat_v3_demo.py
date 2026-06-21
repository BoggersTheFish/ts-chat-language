"""Ten deterministic Habitat v3 demonstrations and evidence export."""

from __future__ import annotations

import json
from pathlib import Path

from ts_vertical_slice.agent_session import HabitatV3Session


ROOT=Path("artifacts/habitat_v3_demo")


def run(name,turns,steps=20,configure=None):
    session=HabitatV3Session(ROOT/name/"receipts")
    print(f"\n=== {name} ===")
    for turn in turns:
        print(f"> {turn}");session.handle(turn,save=False)
    if configure:configure(session)
    receipt=session.run(steps,save=False);print(f"{receipt['decision']['subtype']}: {receipt['rendering']['text']}")
    print("actions:",len(receipt["action_transactions"]),"replans:",receipt["replanning"]["count"],"replay:",receipt["replay"]["final_run_replay_hash"])
    path=ROOT/name/"selected_receipt.json";path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return session,receipt


def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    base=["Alice is in the hall.","The hall connects to the kitchen.","The kitchen connects to the north door.","The red key is in the kitchen.","The red key unlocks the north door.","The north door is locked.","Goal: Open the north door."]
    run("01_topology_aware_execution",base)
    run("02_blocked_direct_route",["The hall connects to the kitchen.","The kitchen connects to the garden.","The hall does not connect to the garden.","Alice is in the hall.","Goal: Move Alice to the garden."])
    run("03_replanning_object_movement",base[:-1]+["After Alice enters the kitchen, Bob takes the red key.",base[-1]])
    run("04_effect_mismatch",["Goal: Activate the alarm."],3,lambda s:s.force_effect_mismatch("activate"))
    run("05_conflicted_topology",["The hall connects to the kitchen.","The hall does not connect to the kitchen.","Alice is in the hall.","Goal: Move Alice to the kitchen."])
    def priorities(session):
        goals=sorted(session.goals.goals.values(),key=lambda item:item.goal_id);session.goals.set_priority(goals[0].goal_id,200,turn=session.turn,source_ids=("demo:priority",));session.goals.set_priority(goals[1].goal_id,100,turn=session.turn,source_ids=("demo:priority",))
    run("06_multiple_goals",["Goal: Activate the alarm.","Goal: Activate the beacon."],10,priorities)
    run("07_impossible_goal",["Alice is in the hall.","The hall connects to the north door.","The north door is locked.","Goal: Open the north door."])
    _,receipt=run("08_multi_agent_interference",base[:-1]+["After Alice enters the kitchen, Bob takes the red key.",base[-1]])
    print("stale causes:",[row["cause"] for row in receipt["replanning"]["events"]])
    run("09_competing_agent_goals",["Alice wants the north door closed.","Bob wants the north door open."])
    print("\n=== 10_reflection_lesson_approval ===")
    session=HabitatV3Session(ROOT/"10_reflection_lesson_approval"/"receipts");session.handle("Goal: Activate the alarm.",save=False);session.force_effect_mismatch("activate");first=session.run(1,save=False);lesson=next(iter(session.loop.run.lessons));print("proposed:",lesson,session.loop.run.lessons[lesson].status);approval=session.approve_lesson(lesson);print("approval:",approval);session.clear_effect_mismatch("activate");final=session.run(8,save=False);print(final["decision"]["subtype"],"policy applied:",any("APPROVED_POLICY_APPLIED" in row["decision"] for row in final["agent_loop"]["steps"]));path=ROOT/"10_reflection_lesson_approval"/"selected_receipt.json";path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(final,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    replay={"scenario":"01_topology_aware_execution","receipt":json.loads((ROOT/"01_topology_aware_execution"/"selected_receipt.json").read_text())};(ROOT/"replay_fixture.json").write_text(json.dumps(replay,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("\nAll ten bounded demonstrations completed.")


if __name__=="__main__":main()
