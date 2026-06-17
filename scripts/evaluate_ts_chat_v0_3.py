#!/usr/bin/env python3
"""Generate TS-Chat v0.3 milestone receipt."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = ROOT / "artifacts"


def main() -> int:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT)
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
    )
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        return proc.returncode

    sys.path.insert(0, str(ROOT))
    from chat.session import TSChatSession
    from ts_lang.meaning_graph import validate_meaning_graph

    session = TSChatSession()
    golden = []
    graph_validations = []
    for text in [
        "nah bro we just want the same usability",
        "nah, im pretty sure we now have the reasoning engine pretty solid",
        "what is next",
    ]:
        receipt = session.handle(text)
        turn = receipt.compiled_turn
        validation = validate_meaning_graph(turn.meaning_graph)
        graph_validations.append(validation.to_dict())
        golden.append(
            {
                "input": text,
                "dialogue_act": turn.dialogue_act,
                "response": receipt.rendered_reply.text,
                "template_id": receipt.rendered_reply.template_id,
                "meaning_graph": turn.meaning_graph.to_dict(),
            }
        )

    receipt = {
        "version": "0.3.0",
        "name": "TS-Chat v0.3 graph-normalized meaning substrate",
        "tests_passed": True,
        "graph_validation_passed": all(item["valid"] for item in graph_validations),
        "graph_validations": graph_validations,
        "acts_supported": [
            "ask_question",
            "answer_simple",
            "correct_assistant",
            "reject_framing",
            "request_plan",
            "continue_topic",
            "express_frustration",
            "confirm_direction",
            "ask_for_definition",
            "ask_for_next_step",
            "strategic_redirect",
        ],
        "golden_traces": golden,
        "boundary": "No transformer, no external LLM, no reasoning engine integration.",
    }

    ARTIFACTS.mkdir(exist_ok=True)
    out = ARTIFACTS / "ts_chat_v0_3_receipt.json"
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())