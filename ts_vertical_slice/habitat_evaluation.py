"""Frozen Habitat v2 functional and adversarial evaluation harness."""
from __future__ import annotations
import argparse,json,time
from collections import Counter,defaultdict
from pathlib import Path
from statistics import mean
from .session import VerticalSliceSession

HARD=("unsupported_accepts","memory_contamination_failures","silent_overwrites","duplicate_semantic_items","irrelevant_cluster_leaks","unsupported_plan_steps","renderer_support_violations","deterministic_replay_failures","execution_errors")

def evaluate(path:Path,out:Path,label:str)->dict:
    cases=[json.loads(line) for line in path.read_text().splitlines() if line.strip()];rows=[];metrics=Counter();timings=[];by_category=defaultdict(Counter)
    for case in cases:
        replays=[];observed=None
        try:
            for replay_index in range(2):
                session=VerticalSliceSession(out/"turns");before_probe=None
                for index,text in enumerate(case["turns"]):
                    if index==len(case["turns"])-1:before_probe=session.state.hash;start=time.perf_counter()
                    receipt=session.handle(text,save=False)
                    if index==len(case["turns"])-1:timings.append((time.perf_counter()-start)*1000)
                replays.append((receipt.deterministic_replay_hash,session.state.hash));observed=receipt
            if len(set(replays))!=1:metrics["deterministic_replay_failures"]+=1
            if case.get("expected_subtype")=="PLAN_VERIFIED" and replays[0]!=replays[1]:metrics["planning_replay_failures"]+=1
            if case["expected_decision"]!="ACCEPT" and observed.final_status=="ACCEPT":metrics["unsupported_accepts"]+=1
            if observed.final_status in {"REJECT","REPAIR"} and before_probe!=session.state.hash:metrics["memory_contamination_failures"]+=1
            if case.get("expect_conflict") and not session.state.world.conflicts():metrics["silent_overwrites"]+=1
            signatures=[(x.kind,x.subject_id,x.predicate,x.object_id,x.polarity,x.operands,x.consequent) for x in session.state.world.items.values()]
            if len(signatures)!=len(set(signatures)):metrics["duplicate_semantic_items"]+=1
            active_predicates={item.get("predicate") for item in (observed.reasoning_request.get("habitat") or {}).get("facts",())}
            if set(case.get("forbidden_active_predicates",()))&active_predicates:metrics["irrelevant_cluster_leaks"]+=1
            if observed.decision_subtype=="REJECT_CONFLICTED" and not observed.contradictions:metrics["conflict_resolution_errors"]+=1
            if observed.decision_subtype=="PLAN_VERIFIED":
                for step in observed.planning.get("chosen_plan",()):
                    if not step.get("support_ids") or not all(check.get("passed") for check in step.get("precondition_checks",())):metrics["unsupported_plan_steps"]+=1
            if case.get("expected_plan_steps") is not None and len(observed.planning.get("chosen_plan",()))!=case["expected_plan_steps"]:metrics["unsupported_plan_steps"]+=1
            if case.get("expect_observation_count"):
                counts=[item.observation_count for item in session.state.world.items.values() if item.kind=="fact"]
                if case["expect_observation_count"] not in counts:metrics["duplicate_semantic_items"]+=1
            decision_ok=observed.final_status==case["expected_decision"]
            subtype_ok=not case.get("expected_subtype") or observed.decision_subtype==case["expected_subtype"]
            answer_ok=all(x.lower() in observed.final_response.lower() for x in case.get("answer_contains",()))
            row={"id":case["id"],"category":case["category"],"expected":case["expected_decision"],"observed":observed.final_status,"subtype":observed.decision_subtype,"response":observed.final_response,"passed":decision_ok and subtype_ok and answer_ok}
            metrics[observed.final_status.lower()+"_count"]+=1;by_category[case["category"]][observed.final_status]+=1
        except AssertionError as exc:
            metrics["renderer_support_violations"]+=1;row={"id":case["id"],"category":case["category"],"passed":False,"error":str(exc)}
        except Exception as exc:
            metrics["execution_errors"]+=1;row={"id":case["id"],"category":case["category"],"passed":False,"error":repr(exc)}
        rows.append(row)
    report={"suite":label,"total_cases":len(cases),"accept_count":metrics["accept_count"],"repair_count":metrics["repair_count"],"reject_count":metrics["reject_count"],**{key:metrics[key] for key in ("unsupported_accepts","memory_contamination_failures","silent_overwrites","duplicate_semantic_items","irrelevant_cluster_leaks","conflict_resolution_errors","unsupported_plan_steps","planning_replay_failures","renderer_support_violations","execution_errors")},"receipt_generation_rate":(len(cases)-metrics["execution_errors"]-metrics["renderer_support_violations"])/len(cases),"deterministic_replay_failures":metrics["deterministic_replay_failures"],"average_processing_time_ms":round(mean(timings),4),"maximum_processing_time_ms":round(max(timings),4),"decision_match_rate":sum(r.get("passed",False) for r in rows)/len(cases),"category_distribution":{k:dict(v) for k,v in sorted(by_category.items())},"results":rows}
    report["all_hard_gates_passed"]=all(report[key]==0 for key in HARD) and report["receipt_generation_rate"]==1.0
    out.mkdir(parents=True,exist_ok=True);(out/f"{label}_report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    lines=[f"# {label.replace('_',' ').title()} report","",f"Cases: {len(cases)}",f"Decisions: ACCEPT {report['accept_count']} / REPAIR {report['repair_count']} / REJECT {report['reject_count']}",f"Decision match rate: {report['decision_match_rate']:.1%}",f"Average / maximum processing time: {report['average_processing_time_ms']} / {report['maximum_processing_time_ms']} ms",f"Receipt generation: {report['receipt_generation_rate']:.1%}",f"Hard gates: {'PASS' if report['all_hard_gates_passed'] else 'FAIL'}","","## Hard-gate metrics","",*[f"- {key}: {report[key]}" for key in HARD],""]
    (out/f"{label}_report.md").write_text("\n".join(lines));return report

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument("--cases",default="evaluation/habitat_v2_cases.jsonl");p.add_argument("--adversarial",default="evaluation/habitat_v2_adversarial.jsonl");p.add_argument("--out",default="artifacts/habitat_v2");a=p.parse_args(argv);out=Path(a.out)
    functional=evaluate(Path(a.cases),out,"habitat_v2_evaluation");adversarial=evaluate(Path(a.adversarial),out,"habitat_v2_adversarial")
    print(json.dumps({"functional":{k:v for k,v in functional.items() if k!="results"},"adversarial":{k:v for k,v in adversarial.items() if k!="results"}},indent=2,sort_keys=True))
    return 0 if functional["all_hard_gates_passed"] and adversarial["all_hard_gates_passed"] else 1
if __name__=="__main__":raise SystemExit(main())
