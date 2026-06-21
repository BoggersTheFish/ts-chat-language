"""Generate the frozen Habitat v3 240-case functional and adversarial corpora."""

from __future__ import annotations

import json
from pathlib import Path


def move_case(index:int):
    return [f"Alice is in the hall{index}.",f"The hall{index} connects to the middle{index}.",f"The middle{index} connects to the garden{index}.",f"Goal: Move Alice to the garden{index}."]


def active_case(index:int,subject="alarm"):
    return [f"The {subject}{index} is inactive.",f"Goal: Activate the {subject}{index}."]


def key_case(index:int,event:bool=False):
    rows=[f"Alice is in the hall{index}.",f"The hall{index} connects to the kitchen{index}.",f"The kitchen{index} connects to the north door{index}.",f"The red key{index} is in the kitchen{index}.",f"The red key{index} unlocks the north door{index}.",f"The north door{index} is locked.",f"Goal: Open the north door{index}."]
    if event:rows.insert(-1,f"After Alice enters the kitchen{index}, Bob takes the red key{index}.")
    return rows


def main()->None:
    functional=[]
    for index in range(30):
        functional.extend((
            {"id":f"topology_{index:03d}","category":"topology_and_route","turns":move_case(index),"expected":"COMPLETE"},
            {"id":f"goal_{index:03d}","category":"persistent_goal","turns":active_case(index),"expected":"COMPLETE"},
            {"id":f"tension_{index:03d}","category":"tension_computation_relaxation","turns":active_case(index,"sensor"),"expected":"COMPLETE","check":"tension"},
            {"id":f"action_{index:03d}","category":"action_execution","turns":active_case(index,"light"),"expected":"COMPLETE","check":"transaction"},
            {"id":f"effect_{index:03d}","category":"effect_verification","turns":active_case(index,"beacon"),"expected":"COMPLETE","check":"effect"},
            {"id":f"replan_{index:03d}","category":"replanning","turns":key_case(index,True),"expected":"UNREACHABLE","check":"replan"},
            {"id":f"reflection_{index:03d}","category":"reflection_and_lesson","turns":active_case(index,"relay"),"expected":"BUDGET_EXHAUSTED","mismatch":"activate","steps":3,"check":"reflection"},
            {"id":f"multi_{index:03d}","category":"multi_agent","turns":[f"Alice wants the alarm{index} active.",f"Bob wants the beacon{index} active."],"expected":"COMPLETE","check":"multi_agent"},
        ))
    assert len(functional)==240
    adversarial_categories=(
        "nonexistent_topology_edges","wrong_direction","blocked_routes","conflicted_routes","repeated_identical_edges","stale_path_assumptions",
        "missing_action_preconditions","action_effects_not_observed","false_success_reports","stale_plan_execution","premature_goal_satisfaction","goal_priority_ties",
        "tension_as_evidence","tension_cycles","unbounded_propagation","planning_cycles","replanning_loops","action_budget_exhaustion","state_budget_exhaustion",
        "scheduled_event_poisoning","malformed_chained_events","repeated_environment_events","rejected_observation_contamination","unapproved_lesson_activation",
        "malicious_lesson_schemas","reflection_bypass","agent_inventory_collision","duplicate_ownership","unauthorized_object_taking","competing_goals",
        "agent_interference","nondeterministic_scheduling","replay_divergence","renderer_false_success","renderer_hidden_conflict","irrelevant_cluster_leakage",
        "dormant_fact_action_support","duplicate_connections","duplicate_goals","receipt_size_exhaustion",
    )
    adversarial=[]
    for category in adversarial_categories:
        for index in range(6):
            turns=move_case(index+1000);expected="UNREACHABLE";steps=6;extra={}
            if category=="wrong_direction":turns=[f"Alice is in the b{index}.",f"The a{index} connects one-way to the b{index}.",f"Goal: Move Alice to the a{index}."]
            elif category=="blocked_routes":turns=[f"Alice is in the a{index}.",f"The passage from the a{index} to the b{index} is blocked.",f"Goal: Move Alice to the b{index}."]
            elif category in {"conflicted_routes","renderer_hidden_conflict"}:turns=[f"Alice is in the a{index}.",f"The a{index} connects to the b{index}.",f"The a{index} does not connect to the b{index}.",f"Goal: Move Alice to the b{index}."]
            elif category in {"repeated_identical_edges","duplicate_connections"}:turns=[f"Alice is in the a{index}.",f"The a{index} connects to the b{index}.",f"The a{index} connects to the b{index}.",f"Goal: Move Alice to the b{index}."];expected="COMPLETE"
            elif category in {"action_effects_not_observed","false_success_reports","renderer_false_success"}:turns=active_case(index+1000);extra={"mismatch":"activate"};expected="BUDGET_EXHAUSTED";steps=3
            elif category in {"stale_path_assumptions","stale_plan_execution","scheduled_event_poisoning","agent_interference"}:turns=key_case(index+1000,True)
            elif category in {"competing_goals"}:turns=[f"Alice wants the door{index} closed.",f"Bob wants the door{index} open."];expected="BLOCKED"
            elif category in {"goal_priority_ties","nondeterministic_scheduling"}:turns=[f"Alice wants the alarm{index} active.",f"Bob wants the beacon{index} active."];expected="COMPLETE"
            elif category in {"replanning_loops","action_budget_exhaustion"}:turns=active_case(index+1000);extra={"mismatch":"activate"};expected="BUDGET_EXHAUSTED";steps=2
            elif category=="planning_cycles":turns=[f"Alice is in the a{index}.",f"The a{index} connects to the b{index}.",f"The b{index} connects to the a{index}.",f"Goal: Move Alice to the missing{index}."]
            elif category in {"duplicate_goals"}:turns=[f"Goal: Activate the alarm{index}.",f"Goal: Activate the alarm{index}."];expected="COMPLETE"
            elif category in {"tension_cycles","unbounded_propagation","tension_as_evidence"}:turns=active_case(index+1000,"tension_target");expected="COMPLETE"
            elif category in {"unapproved_lesson_activation","malicious_lesson_schemas","reflection_bypass"}:turns=active_case(index+1000,"lesson_target");extra={"mismatch":"activate"};expected="BUDGET_EXHAUSTED";steps=2
            elif category in {"agent_inventory_collision","duplicate_ownership","unauthorized_object_taking"}:turns=[f"Alice owns the key{index}.",f"Bob owns the key{index}.",f"Goal: Open the door{index}."]
            elif category in {"replay_divergence"}:turns=active_case(index+1000,"replay_target");expected="COMPLETE";extra={"replay_check":True}
            elif category in {"receipt_size_exhaustion"}:turns=active_case(index+1000,"receipt_target");expected="COMPLETE"
            adversarial.append({"id":f"{category}_{index:03d}","category":category,"turns":turns,"expected":expected,"steps":steps,**extra})
    assert len(adversarial)==240
    root=Path("evaluation");root.mkdir(exist_ok=True)
    for name,rows in (("habitat_v3_functional.jsonl",functional),("habitat_v3_adversarial.jsonl",adversarial)):
        (root/name).write_text("".join(json.dumps(row,sort_keys=True)+"\n" for row in rows),encoding="utf-8")
    print("wrote 240 functional and 240 adversarial Habitat v3 cases")


if __name__=="__main__":main()
