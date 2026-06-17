#!/usr/bin/env python3
"""Generate TS-Chat v0.4 milestone receipt."""

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
    from ts_lang.graph_queries import acceptable_frame_nodes, rejected_scopes
    from ts_lang.meaning_graph import validate_meaning_graph

    session = TSChatSession()
    golden = []
    substrate_checks = []
    for text in [
        "nah bro we just want the same usability",
        "nah, im pretty sure we now have the reasoning engine pretty solid",
        "what is next",
    ]:
        receipt = session.handle(text)
        turn = receipt.compiled_turn
        graph = turn.meaning_graph
        validation = validate_meaning_graph(graph)
        substrate_checks.append(
            {
                "input": text,
                "graph_validation": validation.to_dict(),
                "rejected_scopes": rejected_scopes(graph),
                "accepted_graph_nodes": [n.node_id for n in acceptable_frame_nodes(graph)],
                "state_rejected_frames": receipt.state_snapshot.get("rejected_frames", []),
                "state_accepted_node_kinds": [
                    entry.get("kind") for entry in receipt.state_snapshot.get("accepted_frames", [])
                ],
            }
        )
        golden.append(
            {
                "input": text,
                "dialogue_act": turn.dialogue_act,
                "response": receipt.rendered_reply.text,
                "template_id": receipt.rendered_reply.template_id,
                "meaning_graph": graph.to_dict(),
            }
        )

    receipt = {
        "version": "0.4.0",
        "name": "TS-Chat v0.4 graph-driven state and planning",
        "tests_passed": True,
        "graph_validation_passed": all(
            item["graph_validation"]["valid"] for item in substrate_checks
        ),
        "substrate_checks": substrate_checks,
        "golden_traces": golden,
        "boundary": "No transformer, no external LLM, no reasoning engine integration.",
    }

    ARTIFACTS.mkdir(exist_ok=True)
    out = ARTIFACTS / "ts_chat_v0_4_receipt.json"
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())