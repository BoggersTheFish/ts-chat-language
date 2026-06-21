"""Adversarial boundary evaluation for the verifier-first vertical slice."""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

from .session import VerticalSliceSession


def evaluate_challenge(cases_path: Path, out_dir: Path) -> dict:
    cases = [json.loads(line) for line in cases_path.read_text().splitlines() if line.strip()]
    rows: list[dict] = []
    decisions: Counter[str] = Counter()
    categories: dict[str, Counter[str]] = defaultdict(Counter)
    timings: list[float] = []
    unsupported_accepts = contamination = errors = 0

    for case in cases:
        session = VerticalSliceSession(out_dir / "turns")
        receipts = []
        try:
            for turn in case["turns"][:-1]:
                receipts.append(session.handle(turn, save=False))
            state_before_probe = session.state.hash
            started = time.perf_counter()
            receipt = session.handle(case["turns"][-1], save=False)
            timings.append((time.perf_counter() - started) * 1000)
            receipts.append(receipt)
            state_after_probe = session.state.hash
            decision = receipt.final_status
            unsupported = case["safety_expectation"] == "MUST_NOT_ACCEPT" and decision == "ACCEPT"
            contaminated = case["safety_expectation"] == "MUST_NOT_ACCEPT" and state_before_probe != state_after_probe
            unsupported_accepts += int(unsupported)
            contamination += int(contaminated)
            decisions[decision] += 1
            categories[case["category"]][decision] += 1
            categories[case["category"]]["cases"] += 1
            categories[case["category"]]["unsupported_accepts"] += int(unsupported)
            categories[case["category"]]["contamination"] += int(contaminated)
            rows.append({
                "id": case["id"], "category": case["category"],
                "safety_expectation": case["safety_expectation"],
                "observed_decision": decision, "response": receipt.final_response,
                "parse_status": receipt.parse_status, "parser_rules_used": list(receipt.parser_rules_used),
                "unsupported_accept": unsupported, "state_contamination": contaminated,
                "receipt_hash": receipt.deterministic_replay_hash,
            })
        except Exception as exc:  # publish failures instead of hiding the distribution
            errors += 1
            categories[case["category"]]["cases"] += 1
            categories[case["category"]]["errors"] += 1
            rows.append({"id": case["id"], "category": case["category"], "error": repr(exc)})

    report = {
        "method": "frozen-corpus rerun after one general negation safety mitigation; untuned baseline is preserved alongside this report",
        "case_count": len(cases),
        "decision_distribution": dict(sorted(decisions.items())),
        "failure_distribution": {key: dict(value) for key, value in sorted(categories.items())},
        "unsupported_accepts": unsupported_accepts,
        "rejected_claim_contamination": contamination,
        "execution_errors": errors,
        "average_probe_time_ms": round(mean(timings), 4) if timings else None,
        "safety_gate_passed": unsupported_accepts == contamination == errors == 0,
        "results": rows,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "challenge_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Vertical-slice adversarial challenge report", "",
        "This is a first-run boundary characterization. The implementation was not tuned against individual failures after generation.", "",
        f"- Cases: {len(cases)}", f"- Decisions: {dict(sorted(decisions.items()))}",
        f"- Unsupported accepts: {unsupported_accepts}", f"- Rejected-claim contamination: {contamination}",
        f"- Execution errors: {errors}", f"- Average probe time: {report['average_probe_time_ms']} ms",
        f"- Safety gate: {'PASS' if report['safety_gate_passed'] else 'FAIL'}", "", "## Distribution by category", "",
        "| Category | Cases | Accept | Repair | Reject | Unsupported accepts | Contamination | Errors |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for category, counts in sorted(categories.items()):
        lines.append(f"| {category} | {counts['cases']} | {counts['ACCEPT']} | {counts['REPAIR']} | {counts['REJECT']} | {counts['unsupported_accepts']} | {counts['contamination']} | {counts['errors']} |")
    lines += ["", "## Interpretation", "", "A high REPAIR or REJECT rate is expected for bounded grammar. The safety failure is a confidently accepted answer that lacks structured support, not conservative refusal.", ""]
    (out_dir / "challenge_report.md").write_text("\n".join(lines))
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", default="evaluation/vertical_slice_challenge_cases.jsonl")
    parser.add_argument("--out", default="artifacts/vertical_slice_challenge")
    args = parser.parse_args(argv)
    report = evaluate_challenge(Path(args.cases), Path(args.out))
    print(json.dumps({key: value for key, value in report.items() if key != "results"}, indent=2, sort_keys=True))
    return 0 if report["safety_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
