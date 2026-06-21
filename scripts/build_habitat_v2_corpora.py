#!/usr/bin/env python3
"""Generate frozen Habitat v2 functional and adversarial corpora."""
from __future__ import annotations
import json
from pathlib import Path

functional=[]; adversarial=[]
def add(rows,category,turns,decision,**extra):
    n=sum(x["category"]==category for x in rows)+1
    rows.append({"id":f"{category}_{n:03d}","category":category,"turns":turns,"expected_decision":decision,**extra})

states=[("open","open"),("locked","locked"),("armed","armed"),("active","active")]
for i in range(20):
    subject=f"device{i}";state,_=states[i%4]
    add(functional,"semantic_merge",[f"The {subject} is {state}.",f"The {subject} is {state}.",f"Is the {subject} {state}?"],"ACCEPT",expect_observation_count=2)
for i in range(20):
    a,b=f"Alice{i}",f"Bob{i}";subject=f"door{i}"
    add(functional,"cluster_relevance",[f"{a} is older than {b}.",f"The {subject} is open.",f"Is the {subject} open?"],"ACCEPT",forbidden_active_predicates=["older_than"])
for i in range(5):
    add(functional,"signed_state",[f"The gate{i} is open.",f"Is the gate{i} open?"],"ACCEPT",expected_subtype="CONCLUSION_VERIFIED")
    add(functional,"signed_state",[f"The gate{i} is not open.",f"Is the gate{i} open?"],"ACCEPT",answer_contains=["not open"])
    add(functional,"signed_state",[f"The gate{i} is open.",f"The gate{i} is not open.",f"Is the gate{i} open?"],"REJECT",expected_subtype="REJECT_CONFLICTED",expect_conflict=True)
    add(functional,"signed_state",[f"Is the unknown_gate{i} open?"],"REJECT",expected_subtype="REJECT_UNSUPPORTED")
for i in range(10):
    action="opens" if i%2==0 else "closes";initial="closed" if action=="opens" else "open";needle="is open" if action=="opens" else "not open"
    add(functional,"event_transition",[f"The door{i} is {initial}.",f"Alice{i} {action} the door{i}.",f"Is the door{i} open?"],"ACCEPT",answer_contains=[needle])
for i in range(5):
    add(functional,"event_transition",[f"Alice{i} owns the red key {i}.",f"Alice{i} gives the red key {i} to Sarah{i}.",f"Who owns the red key {i}?"],"ACCEPT",answer_contains=[f"Sarah{i}"])
for i in range(5):
    add(functional,"event_transition",[f"The key{i} is inside the box{i}.",f"The box{i} is in the kitchen{i}.",f"Where is the key{i}?"],"ACCEPT",answer_contains=[f"box{i}",f"kitchen{i}"])
for i in range(20):
    add(functional,"causal_chain",[f"If the door{i} opens, the sensor{i} activates. If the sensor{i} activates and the system{i} is armed, the alarm{i} activates. The door{i} opens. The system{i} is armed. Is the alarm{i} active?"],"ACCEPT",answer_contains=[f"alarm{i}","active"],expected_derivations=2)
for i in range(10):
    add(functional,"verified_planning",[f"Alice{i} is in the hall{i}.",f"The box{i} is in the kitchen{i}.",f"The red key {i} is inside the box{i}.",f"The north door {i} is locked.",f"The red key {i} unlocks the north door {i}.",f"How can Alice{i} open the north door {i}?"],"ACCEPT",expected_subtype="PLAN_VERIFIED",expected_plan_steps=5)
for i in range(10):
    add(functional,"verified_planning",[f"Alice{i} is in the hall{i}.",f"The north door {i} is locked.",f"How can Alice{i} open the north door {i}?"],"REJECT",expected_subtype="REJECT_UNREACHABLE")

for i in range(6):
    add(adversarial,"contradictory_facts",[f"The door{i} is open.",f"The door{i} is not open.",f"Is the door{i} open?"],"REJECT",expect_conflict=True)
    add(adversarial,"stale_state",[f"The door{i} is closed.",f"Alice{i} opens the door{i}.",f"Bob{i} closes the door{i}.",f"Is the door{i} open?"],"ACCEPT",answer_contains=["not open"])
    add(adversarial,"repeated_events",[f"The door{i} is closed.",f"Alice{i} opens the door{i}.",f"Alice{i} opens the door{i}.",f"Is the door{i} open?"],"ACCEPT")
    add(adversarial,"repeated_rules",[f"If the door{i} opens, the sensor{i} activates.",f"If the door{i} opens, the sensor{i} activates.",f"The door{i} opens.",f"Is the sensor{i} active?"],"ACCEPT")
    add(adversarial,"impossible_plans",[f"Alice{i} is in the hall{i}.",f"The door{i} is locked.",f"How can Alice{i} open the door{i}?"],"REJECT")
    add(adversarial,"missing_keys",[f"Alice{i} is in the hall{i}.",f"The door{i} is locked.",f"How can Alice{i} open the door{i}?"],"REJECT")
    add(adversarial,"wrong_keys",[f"Alice{i} is in the hall{i}.",f"The blue key {i} is inside the box{i}.",f"The red key {i} unlocks the door{i}.",f"The door{i} is locked.",f"How can Alice{i} open the door{i}?"],"REJECT")
    add(adversarial,"ambiguous_ownership",[f"Alice{i} gave Sarah{i} her key. Who owns the key?"],"REPAIR")
    add(adversarial,"unsupported_locations",[f"Alice{i} is somewhere near the hall. How can Alice{i} open the door{i}?"],"REPAIR")
    add(adversarial,"causal_cycles",[f"If the sensor{i} activates, the alarm{i} activates. If the alarm{i} activates, the sensor{i} activates. Is the alarm{i} active?"],"REJECT")
    add(adversarial,"negated_preconditions",[f"The door{i} is not locked. How can Alice{i} open the door{i}?"],"REJECT")
    add(adversarial,"malformed_events",[f"Alice{i} opens gives door maybe."],"REPAIR")
    add(adversarial,"irrelevant_clusters",[f"Alice{i} is older than Bob{i}.",f"The alarm{i} is active.",f"Is the alarm{i} active?"],"ACCEPT",forbidden_active_predicates=["older_than"])
    add(adversarial,"rejected_contamination",[f"Alice{i} gives the key{i} to Sarah{i}.",f"Who owns the key{i}?"],"REJECT")
    add(adversarial,"renderer_overstatement",[f"Is the door{i} open?"],"REJECT")
    add(adversarial,"superseded_state_reuse",[f"The door{i} is open.",f"Bob{i} closes the door{i}.",f"Is the door{i} open?"],"ACCEPT",answer_contains=["not open"])
    add(adversarial,"planning_precondition_bypass",[f"The red key {i} unlocks the door{i}.",f"The door{i} is locked.",f"How can Alice{i} open the door{i}?"],"REJECT")

assert len(functional)==120,len(functional)
assert len(adversarial)==102,len(adversarial)
Path("evaluation/habitat_v2_cases.jsonl").write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in functional))
Path("evaluation/habitat_v2_adversarial.jsonl").write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in adversarial))
print(f"wrote {len(functional)} functional and {len(adversarial)} adversarial cases")
