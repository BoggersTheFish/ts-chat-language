"""Utterance normalizer for messy human input."""

from __future__ import annotations

import re

from ts_lang.markers import detect_markers
from ts_lang.types import NormalizedUtterance

MULTISPACE_RE = re.compile(r"\s+")
REPEAT_PUNCT_RE = re.compile(r"([!?.,;:]){2,}")


def normalize_utterance(raw: str) -> NormalizedUtterance:
    text = raw.strip()
    collapsed = MULTISPACE_RE.sub(" ", text)
    collapsed = REPEAT_PUNCT_RE.sub(r"\1", collapsed)
    clean = collapsed.lower()
    tokens = [t for t in re.split(r"\s+", clean) if t]

    markers = detect_markers(raw, clean)

    return NormalizedUtterance(
        raw=raw,
        clean=clean,
        tokens=tokens,
        markers=markers,
    )