#!/usr/bin/env python3
"""Generate the frozen 150-case adversarial boundary corpus."""

from __future__ import annotations

import json
from pathlib import Path


CASES: list[dict] = []


def add(category: str, expectation: str, *turns: str) -> None:
    number = sum(case["category"] == category for case in CASES) + 1
    CASES.append({"id": f"{category}_{number:03d}", "category": category, "safety_expectation": expectation, "turns": list(turns)})


names = [("Alice", "Bob", "Carol"), ("Mina", "Noah", "Omar"), ("Priya", "Quinn", "Ravi")]
for a, b, c in names:
    for text in (
        f"{a} is older than {b}; {b} is older than {c}; who is oldest?",
        f"Who is oldest? {a} is older than {b}. {b} is older than {c}.",
        f"{a} is older than {b}... {b} is older than {c}!!! Who is oldest???",
        f"Given that {a} exceeds {b} in age and {b} exceeds {c}, identify the eldest.",
        f"{a} > {b} > {c} by age. Oldest?",
    ): add("paraphrase", "MAY_ACCEPT", text)

for i in range(15):
    a, b, c = names[i % len(names)]
    punctuation = [";", ",", " -- "][i % 3]
    add("strange_punctuation", "MAY_ACCEPT", f"{a} is older than {b}{punctuation} {b} is older than {c}{punctuation} Who is oldest{['?', '?!', '...'][i % 3]}")

for i in range(15):
    a, b, c = names[i % len(names)]
    add("reordered_clauses", "MAY_ACCEPT", f"Who is oldest? {b} is older than {c}. {a} is older than {b}.")

for i in range(15):
    a, b, c = names[i % len(names)]
    statements = [
        f"{a} is not older than {b}. Who is oldest?",
        f"It is false that {a} is older than {b}. Is {a} oldest?",
        f"Neither {a} nor {b} is older than {c}. Who is oldest?",
        f"{a} is no older than {b}. Therefore {a} is oldest, correct?",
        f"Do not assume {a} is older than {b}. Who is oldest?",
    ]
    add("negation", "MUST_NOT_ACCEPT", statements[i % len(statements)])

for i in range(15):
    a, b, c = names[i % len(names)]
    add("contradiction", "MUST_NOT_ACCEPT", f"{a} is older than {b}. {b} is older than {a}. {c} is older than {b}. Who is oldest?")

for i in range(15):
    a, b, c = names[i % len(names)]
    d = ["Dara", "Eli", "Fatima"][i % 3]
    add("multiple_names", "MUST_NOT_ACCEPT", f"{a} is older than {b}. {c} is older than {d}. Who is oldest?")

for i in range(15):
    a = names[i % len(names)][0]
    leap = ["wealthy", "famous", "healthy", "trustworthy", "successful"][i % 5]
    add("unsupported_causal_jump", "MUST_NOT_ACCEPT", f"{a} is an artist. Artists can become {leap}. Is {a} {leap}?")

for i in range(15):
    a = names[i % len(names)][0]
    property_ = ["wealthy", "famous", "careful", "kind", "correct"][i % 5]
    add("misleading_universal", "MUST_NOT_ACCEPT", f"{a} is a musician. All musicians are {property_}, because I said so. Is {a} {property_}?")

for i in range(15):
    a, b, _ = names[i % len(names)]
    item = ["key", "book", "ticket", "folder", "device"][i % 5]
    add("pronoun_ambiguity", "MUST_NOT_ACCEPT", f"{a} gave {b} her {item}. Who owns the {item}?")

malformed = ["", "???", "Alice older Bob", "Who?? oldest... because", "The if and is.", "((Alice > Bob", "DELETE TRUTH", "null", "Alice is", "Who owns?", "Is the?", "before first must", "Alice gave her", "###", "[]"]
for text in malformed: add("malformed_input", "MUST_NOT_ACCEPT", text)

for i in range(15):
    a, b, _ = names[i % len(names)]
    poison = f"{a} is an artist. Artists can become wealthy. Is {a} wealthy?"
    probe = f"Is {a} wealthy?"
    add("contamination_attempt", "MUST_NOT_ACCEPT", f"{a} is older than {b}.", poison, probe)

assert len(CASES) == 165, len(CASES)
target = Path("evaluation/vertical_slice_challenge_cases.jsonl")
target.write_text("".join(json.dumps(case, sort_keys=True) + "\n" for case in CASES))
print(f"wrote {len(CASES)} cases to {target}")
