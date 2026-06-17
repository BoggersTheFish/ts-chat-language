"""Load compiled language resources from data/*.json."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=8)
def load_json(name: str) -> dict:
    path = DATA_DIR / name
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def dialogue_acts() -> list[dict]:
    return load_json("dialogue_acts.json")["acts"]


def phrase_patterns() -> list[dict]:
    return load_json("phrase_patterns.json")["phrases"]


def frame_schemas() -> dict:
    return load_json("semantic_frame_schemas.json")["schemas"]


def render_templates() -> list[dict]:
    return load_json("render_templates.json")["templates"]


def lexicon() -> dict:
    return load_json("lexicon.json")