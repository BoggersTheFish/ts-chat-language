"""Detect discourse markers in normalized text."""

from __future__ import annotations

import re

from ts_lang.types import MarkerSet

NEGATION_RE = re.compile(
    r"\b(?:nah|nope|no|not|don't|do not|never|ain't)\b",
    re.IGNORECASE,
)
FRUSTRATION_RE = re.compile(
    r"\b(?:fuck(?:ing)?|shit|damn|stop|ffs|for fuck'?s sake)\b",
    re.IGNORECASE,
)
COMMAND_RE = re.compile(
    r"\b(?:build|stop|do|make|give|show|start|fix|focus)\b",
    re.IGNORECASE,
)
CAPS_WORD_RE = re.compile(r"\b[A-Z]{2,}\b")


def caps_emphasis_ratio(raw: str) -> float:
    words = re.findall(r"[A-Za-z]+", raw)
    if not words:
        return 0.0
    caps = sum(1 for w in words if w.isupper() and len(w) > 1)
    return caps / len(words)


def detect_markers(raw: str, clean: str) -> MarkerSet:
    negation = bool(NEGATION_RE.search(clean))
    frustration = bool(FRUSTRATION_RE.search(clean))
    command = bool(COMMAND_RE.search(clean))
    caps_ratio = caps_emphasis_ratio(raw)

    intensity = 0.2
    if negation:
        intensity += 0.15
    if frustration:
        intensity += 0.45
    if command:
        intensity += 0.1
    if caps_ratio > 0.2:
        intensity += min(0.3, caps_ratio)

    return MarkerSet(
        negation=negation,
        frustration=frustration,
        command=command,
        intensity=min(1.0, round(intensity, 2)),
        caps_emphasis=caps_ratio > 0.2,
    )