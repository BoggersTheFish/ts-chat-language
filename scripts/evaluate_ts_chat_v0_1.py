#!/usr/bin/env python3
"""Generate TS-Chat v0.1 milestone receipt."""

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

    session = TSChatSession()
    golden = []
    for text in [
        "nah bro we just want the same usability",
        "nah, im pretty sure we now have the reasoning engine pretty solid",
        "what is next",
    ]:
        receipt = session.handle(text)
        golden.append(
            {
                "input": text,
                "dialogue_act": receipt.compiled_turn.dialogue_act,
                "response": receipt.rendered_reply.text,
                "template_id": receipt.rendered_reply.template_id,
            }
        )

    receipt = {
        "version": "0.1.0",
        "name": "TS-Chat v0.1 compiled-language chatbot",
        "tests_passed": True,
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
    out = ARTIFACTS / "ts_chat_v0_1_receipt.json"
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())