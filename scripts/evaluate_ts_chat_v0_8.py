#!/usr/bin/env python3
"""Generate TS-Chat v0.8 milestone receipt."""

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
    from ts_lang.dialogue_act import compile_dialogue_act
    from ts_lang.normalize import normalize_utterance
    from ts_lang.resources import active_packs, graph_rules, pack_info, topic_rules
    from ts_lang.semantic_frame import last_fired_rule_ids

    session = TSChatSession()
    golden = []
    for text in [
        "nah bro we just want the same usability",
        "nah, im pretty sure we now have the reasoning engine pretty solid",
        "what is next",
    ]:
        receipt = session.handle(text)
        turn = receipt.compiled_turn
        utterance = normalize_utterance(text)
        act = compile_dialogue_act(utterance)
        golden.append(
            {
                "input": text,
                "dialogue_act": turn.dialogue_act,
                "response": receipt.rendered_reply.text,
                "template_id": receipt.rendered_reply.template_id,
                "rule_ids_fired": last_fired_rule_ids(utterance, act),
                "frame_schemas": [frame.schema for frame in turn.semantic_frames],
            }
        )

    receipt = {
        "version": "0.8.0",
        "name": "TS-Chat v0.8 declarative graph and topic rules",
        "tests_passed": True,
        "active_packs": active_packs(),
        "pack_info": pack_info(),
        "graph_rule_ids": [rule["id"] for rule in graph_rules()],
        "topic_rule_ids": [rule["id"] for rule in topic_rules()],
        "golden_traces": golden,
        "boundary": "No transformer, no external LLM, no reasoning engine integration.",
    }

    ARTIFACTS.mkdir(exist_ok=True)
    out = ARTIFACTS / "ts_chat_v0_8_receipt.json"
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())