"""Interactive TS-Chat CLI."""

from __future__ import annotations

import argparse
import json
import os
import sys

from chat.session import TSChatSession
from ts_lang.resources import active_packs, reload_resources

DEMO_SCRIPT = [
    "nah bro we just want the same usability",
    "nah, im pretty sure we now have the reasoning engine pretty solid",
    "what is next",
]


def _configure_packs(packs: str | None) -> None:
    if packs:
        os.environ["TSLC_PACKS"] = packs
    reload_resources()


def run_demo() -> None:
    session = TSChatSession()
    print(f"TS-Chat v0.7 demo (packs: {', '.join(active_packs())})\n")
    for text in DEMO_SCRIPT:
        receipt = session.handle(text)
        print(f"User: {text}")
        print(f"Bot:  {receipt.rendered_reply.text}\n")


def run_repl() -> None:
    session = TSChatSession()
    print(
        f"TS-Chat v0.7 (TSLC). Packs: {', '.join(active_packs())}. "
        "Type 'quit' to exit, 'state' for JSON state, 'trace' for last receipt.\n"
    )
    while True:
        try:
            line = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line.lower() in {"quit", "exit"}:
            break
        if line.lower() == "state":
            print(json.dumps(session.state.to_dict(), indent=2))
            continue
        if line.lower() == "trace":
            if session.last_receipt is None:
                print("No turns yet.")
            else:
                print(json.dumps(session.last_receipt.to_dict(), indent=2))
            continue

        receipt = session.handle(line)
        print(f"Bot> {receipt.rendered_reply.text}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TS-Chat v0.7 — TSLC conversational shell")
    parser.add_argument("--demo", action="store_true", help="Run scripted demo conversation")
    parser.add_argument(
        "--packs",
        default=None,
        help="Comma-separated pack list (default: base_dialogue,ts_architecture)",
    )
    args = parser.parse_args(argv)
    _configure_packs(args.packs)

    if args.demo:
        run_demo()
    else:
        run_repl()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())