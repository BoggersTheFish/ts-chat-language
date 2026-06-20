"""Machine-readable evaluation harness for the vertical slice."""

from __future__ import annotations

import argparse, json, time
from pathlib import Path
from statistics import mean
from .session import VerticalSliceSession


def evaluate(cases_path: Path, out_dir: Path):
    cases=[json.loads(line) for line in cases_path.read_text().splitlines() if line.strip()]; rows=[]; timings=[]
    unsupported=contamination=replay_failures=renderer_violations=schema_failures=receipt_failures=repair_success=unresolved=0
    for case in cases:
        hashes=[]; receipt=None; before=None; after=None
        try:
            for _ in range(3):
                session=VerticalSliceSession(out_dir/"turns"); before=session.state.hash; start=time.perf_counter(); current=session.handle(case["input"],save=False); timings.append((time.perf_counter()-start)*1000); after=session.state.hash; hashes.append(current.deterministic_replay_hash); receipt=current
            decision_ok=receipt.final_status==case["expected_decision"]
            answer_ok=all(x.lower() in receipt.final_response.lower() for x in case.get("expected_answer_contains",[])) and all(x.lower() not in receipt.final_response.lower() for x in case.get("forbidden_answer_contains",[]))
            checks={x["check_id"] for x in receipt.verifier_checks}; checks_ok=all(x in checks for x in case.get("expected_checks",[]))
            if len(set(hashes))!=1: replay_failures+=1
            if case["expected_decision"]!="ACCEPT" and receipt.final_status=="ACCEPT": unsupported+=1
            if receipt.final_status in {"REJECT","REPAIR"} and before!=after: contamination+=1
            if receipt.final_status=="REPAIR" and receipt.repair_result in {"REPAIR_ACCEPTED","REPAIR_NEEDS_USER"}: repair_success+=1
            if receipt.repair_result=="REPAIR_NEEDS_USER": unresolved+=1
            row={"id":case["id"],"expected_decision":case["expected_decision"],"observed_decision":receipt.final_status,"response":receipt.final_response,"decision_ok":decision_ok,"answer_ok":answer_ok,"checks_ok":checks_ok,"passed":decision_ok and answer_ok and checks_ok and len(set(hashes))==1}
        except AssertionError as exc: renderer_violations+=1; row={"id":case["id"],"passed":False,"error":str(exc)}
        except Exception as exc: schema_failures+=1; row={"id":case["id"],"passed":False,"error":repr(exc)}
        rows.append(row)
    receipt_success=len(cases)-receipt_failures-schema_failures-renderer_violations
    report={"case_count":len(cases),"decision_accuracy":sum(r.get("decision_ok",False) for r in rows)/len(cases),"unsupported_accepts":unsupported,"rejected_claim_contamination":contamination,"repair_success_count":repair_success,"unresolved_ambiguity_count":unresolved,"deterministic_replay_failures":replay_failures,"renderer_support_violations":renderer_violations,"schema_failures":schema_failures,"average_processing_time_ms":round(mean(timings),4),"receipt_generation_success":receipt_success/len(cases),"results":rows}
    report["all_hard_gates_passed"]=unsupported==contamination==replay_failures==renderer_violations==schema_failures==0 and report["receipt_generation_success"]==1.0 and all(r["passed"] for r in rows)
    out_dir.mkdir(parents=True,exist_ok=True); (out_dir/"evaluation_report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    md=["# Vertical-slice evaluation","",f"Cases: {len(cases)}",f"Decision accuracy: {report['decision_accuracy']:.1%}",f"Unsupported accepts: {unsupported}",f"Rejected-claim contamination: {contamination}",f"Replay failures: {replay_failures}",f"Renderer support violations: {renderer_violations}",f"Receipt generation success: {report['receipt_generation_success']:.1%}",f"Average processing time: {report['average_processing_time_ms']} ms",f"Hard gates: {'PASS' if report['all_hard_gates_passed'] else 'FAIL'}",""]
    (out_dir/"evaluation_report.md").write_text("\n".join(md)); return report


def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--cases",default="evaluation/vertical_slice_cases.jsonl");p.add_argument("--out",default="artifacts/vertical_slice");a=p.parse_args(argv)
    report=evaluate(Path(a.cases),Path(a.out));print(json.dumps(report,indent=2,sort_keys=True));return 0 if report["all_hard_gates_passed"] else 1
if __name__=="__main__": raise SystemExit(main())
