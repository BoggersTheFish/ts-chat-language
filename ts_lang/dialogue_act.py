"""Pattern-backed dialogue act compiler."""

from __future__ import annotations

import re
from typing import Any

from ts_lang.resources import dialogue_acts, phrase_patterns
from ts_lang.types import DialogueActResult, NormalizedUtterance


def _score_act(act: dict, text: str) -> tuple[float, str | None]:
    best = 0.0
    subact = act["subacts"][0] if act.get("subacts") else None
    for pattern in act.get("patterns", []):
        if re.search(pattern, text, re.IGNORECASE):
            best = max(best, float(act.get("weight", 0.5)))
    return best, subact


def _phrase_boosts(text: str) -> list[tuple[str, float, dict[str, Any]]]:
    hits: list[tuple[str, float, dict[str, Any]]] = []
    for entry in phrase_patterns():
        pattern = entry.get("pattern") or entry.get("phrase", "")
        if pattern and re.search(pattern, text, re.IGNORECASE):
            meaning = dict(entry.get("meaning", {}))
            act = meaning.pop("act", "continue_topic")
            hits.append((act, 0.95, meaning))
    return hits


def _emotion_from_markers(utterance: NormalizedUtterance, meaning: dict[str, Any]) -> dict[str, Any]:
    emotion: dict[str, Any] = {}
    if utterance.markers.frustration:
        emotion["affect"] = "frustrated"
        emotion["intensity"] = max(utterance.markers.intensity, float(meaning.get("intensity", 0.0)))
    elif utterance.markers.negation:
        emotion["affect"] = "corrective"
        emotion["intensity"] = utterance.markers.intensity
    if meaning.get("tone"):
        emotion["tone"] = meaning["tone"]
    return emotion


def compile_dialogue_act(
    utterance: NormalizedUtterance,
    *,
    current_topic: str | None = None,
    rejected_frames: list[str] | None = None,
) -> DialogueActResult:
    text = utterance.clean
    scores: dict[str, float] = {}
    subacts: dict[str, str | None] = {}
    meanings: dict[str, dict[str, Any]] = {}
    ambiguities: list[str] = []

    for act in dialogue_acts():
        score, subact = _score_act(act, text)
        if score > 0:
            scores[act["id"]] = score
            subacts[act["id"]] = subact
            meanings[act["id"]] = {"description": act.get("description", "")}

    for act_id, boost, meaning in _phrase_boosts(text):
        scores[act_id] = max(scores.get(act_id, 0.0), boost)
        meanings[act_id] = {**meanings.get(act_id, {}), **meaning}
        if meaning.get("requires_reframe"):
            subacts[act_id] = "understanding_correction"

    if utterance.markers.frustration and "express_frustration" not in scores:
        scores["express_frustration"] = max(0.7, utterance.markers.intensity)

    if not scores:
        if "?" in utterance.raw:
            scores["ask_question"] = 0.55
        else:
            scores["continue_topic"] = 0.4
            ambiguities.append("no_strong_act_pattern")

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    top_act, top_score = ranked[0]
    if len(ranked) > 1 and ranked[1][1] >= top_score - 0.05:
        ambiguities.append(f"tie_between_{top_act}_and_{ranked[1][0]}")

    meaning = dict(meanings.get(top_act, {}))
    if current_topic and top_act in {"continue_topic", "correct_assistant"}:
        meaning.setdefault("topic", current_topic)
    if rejected_frames:
        meaning.setdefault("rejected_context", list(rejected_frames))

    emotion = _emotion_from_markers(utterance, meaning)

    return DialogueActResult(
        act=top_act,
        subact=subacts.get(top_act),
        meaning=meaning,
        emotion=emotion,
        confidence=round(min(1.0, top_score), 2),
        ambiguities=ambiguities,
    )