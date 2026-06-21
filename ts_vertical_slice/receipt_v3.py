"""Additive ts-turn-receipt-v3 construction and whole-run replay evidence."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ts_reasoner.typed_support import canonical_hash


REQUIRED_SECTIONS = (
    "turn","parse","meaning_graph","semantic_merge","cluster_activation","signed_world_state",
    "goals","tension","planning","agent_loop","action_transactions","environment_events",
    "replanning","reflection","lessons","multi_agent","decision","rendering","memory_update","replay",
)


def build_v3_receipt(*, turn:dict[str,Any], parse:dict[str,Any], session:"Any") -> dict[str,Any]:
    loop=session.loop;run=loop.run if loop else None;world=loop.world if loop else None
    payload={
        "receipt_schema":"ts-turn-receipt-v3",
        "turn":turn,
        "parse":parse,
        "meaning_graph":{"nodes":parse.get("directives",()),"edge_count":0,"graph_hash":canonical_hash(parse)},
        "semantic_merge":session.last_merge,
        "cluster_activation":run.loop_steps[-1] if run and run.loop_steps and run.loop_steps[-1]["phase"]=="ACTIVATE_CLUSTER" else {},
        "signed_world_state":{key:value.__dict__ for key,value in sorted((world.signed_state if world else {}).items())},
        "goals":{"items":session.goals.to_dict(),"verifications":[item.__dict__ for item in session.goals.verifications]},
        "tension":loop.tension.to_dict() if loop else {},
        "planning":{"plans":[_plan(item) for item in (run.plans if run else ())],"selected_plan_id":loop.current_plan.plan_id if loop and loop.current_plan else ""},
        "agent_loop":{"state":run.outcome if run else "IDLE","iterations":loop.iterations if loop else 0,"steps":run.loop_steps if run else []},
        "action_transactions":run.action_transactions if run else [],
        "environment_events":run.environment_events if run else [],
        "replanning":{"count":len(run.replanning) if run else 0,"events":run.replanning if run else []},
        "reflection":{"records":[item.__dict__ for item in (run.reflections if run else ())]},
        "lessons":{"items":{key:value.__dict__ for key,value in sorted((run.lessons if run else {}).items())},"approval_receipts":session.lesson_receipts},
        "multi_agent":{"agents":[item.__dict__ for item in sorted(session.environment.snapshot().agents,key=lambda value:value.agent_id)],"scheduling_policy":"priority_then_tension_then_agent_id"},
        "decision":session.last_decision,
        "rendering":session.last_rendering,
        "memory_update":session.last_memory_update,
        "replay":{"initial_environment_snapshot_hash":run.initial_snapshot_hash if run else canonical_hash(asdict(session.environment.snapshot())),"input_sequence_hash":canonical_hash(session.input_sequence),"scheduled_events_hash":canonical_hash([asdict(item) for item in session.environment.snapshot().scheduled_events]),"approved_lessons_hash":canonical_hash([key for key,value in sorted((run.lessons if run else {}).items()) if value.status=="APPROVED"]),"configuration":run.configuration.__dict__ if run else session.limits.__dict__,"compatible_repository_shas":session.repository_shas,"final_run_replay_hash":run.final_replay_hash if run else ""},
    }
    payload["receipt_hash"]=canonical_hash(payload)
    return payload


def _plan(plan:Any)->dict[str,Any]:
    value=plan.__dict__.copy();value["actions"]=[item.__dict__|{"preconditions":[x.__dict__ for x in item.preconditions],"expected_effects":[x.__dict__ for x in item.expected_effects]} for item in plan.actions];return value


def write_v3_receipt(receipt:dict[str,Any],root:Path)->Path:
    root.mkdir(parents=True,exist_ok=True);identity=receipt["receipt_hash"][:12];path=root/f"{receipt['turn']['turn_id']}_{identity}.json";text=json.dumps(receipt,indent=2,sort_keys=True)+"\n"
    if len(text.encode())>receipt["replay"]["configuration"]["max_receipt_size"]:raise OverflowError("MAX_RECEIPT_SIZE")
    path.write_text(text,encoding="utf-8");return path
