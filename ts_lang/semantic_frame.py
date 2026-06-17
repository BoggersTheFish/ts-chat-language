"""Semantic frame compiler from dialogue acts and lexicon hits."""

from __future__ import annotations

import re
from typing import Any

from ts_lang.resources import lexicon
from ts_lang.types import DialogueActResult, NormalizedUtterance, SemanticFrame


def _topic_hits(text: str) -> tuple[list[str], list[str]]:
    known: list[str] = []
    unknown: list[str] = []
    topics = lexicon().get("topics", {})
    for topic, keywords in topics.items():
        for kw in keywords:
            if kw.lower() in text:
                known.append(topic)
                break
    if not known and len(text.split()) > 6:
        unknown.append("unmapped_phrasing")
    return known, unknown


def _provenance(builder: str, *, pattern: str | None = None) -> dict[str, Any]:
    prov: dict[str, Any] = {"source_type": "frame_builder", "source_id": builder}
    if pattern:
        prov["pattern"] = pattern
    return prov


def _emotion_frame(utterance: NormalizedUtterance, act: DialogueActResult) -> SemanticFrame | None:
    if not act.emotion:
        return None
    return SemanticFrame(
        schema="emotion_frame",
        slots={
            "affect": act.emotion.get("affect", "neutral"),
            "intensity": act.emotion.get("intensity", utterance.markers.intensity),
            "tone": act.emotion.get("tone", "neutral"),
        },
        provenance=_provenance("emotion_frame"),
    )


def _claim_frame(text: str, act: DialogueActResult) -> SemanticFrame | None:
    if "train" in text and ("don't" in text or "do not" in text or "dont" in text):
        return SemanticFrame(
            schema="claim",
            slots={
                "subject": "TS chatbot",
                "predicate": "does_not_require_training_for_language",
                "reason": "language_can_be_compiled_into_TS",
            },
            provenance=_provenance("claim_frame", pattern="dont_need_to_train"),
        )
    if act.meaning.get("claim"):
        return SemanticFrame(
            schema="claim",
            slots={
                "subject": act.meaning.get("desired_focus", "conversation"),
                "predicate": act.meaning["claim"],
                "reason": act.meaning.get("reason", ""),
            },
            provenance=_provenance("claim_frame", pattern="phrase_meaning.claim"),
        )
    return None


def _architecture_frame(text: str) -> SemanticFrame | None:
    avoid: list[str] = []
    prefer: list[str] = []
    if re.search(r"\b(?:transformer|token prediction|train(?:ing)?(?:\s+it)?\s+on\s+data|exposure|dont need to train)\b", text):
        avoid.extend(["exposure_training", "normal_transformer"])
    if re.search(r"\b(?:compile|compiler|ts state|meaning graph|language machine)\b", text):
        prefer.append("language_to_TS_compilation")
    if re.search(r"\b(?:chatbot|usability|normal chat)\b", text):
        prefer.append("chatbot_usability_surface")
    if not avoid and not prefer:
        return None
    return SemanticFrame(
        schema="architecture_preference",
        slots={"avoid": avoid, "prefer": prefer},
        provenance=_provenance("architecture_frame"),
    )


def _scope_frame(act: DialogueActResult) -> SemanticFrame | None:
    meaning = act.meaning
    if act.act not in {"correct_assistant", "reject_framing", "strategic_redirect"}:
        return None
    rejects = []
    if meaning.get("rejects"):
        rej = meaning["rejects"]
        if isinstance(rej, list):
            rejects.extend(rej)
        else:
            rejects.append(rej)
    if meaning.get("deprioritize"):
        dep = meaning["deprioritize"]
        if isinstance(dep, list):
            rejects.extend(dep)
        else:
            rejects.append(dep)
    if meaning.get("rejected_context"):
        rejects.extend(meaning["rejected_context"])
    accepts = []
    if meaning.get("desired_focus"):
        accepts.append(meaning["desired_focus"])
    if meaning.get("new_focus"):
        accepts.append(meaning["new_focus"])
    if not rejects and not accepts:
        return None
    return SemanticFrame(
        schema="scope_correction",
        slots={
            "rejects": rejects,
            "accepts": accepts,
            "desired_focus": meaning.get("desired_focus") or meaning.get("new_focus"),
        },
        provenance=_provenance("scope_frame", pattern="phrase_meaning.scope"),
    )


def _usability_frame(text: str) -> SemanticFrame | None:
    if not re.search(r"\b(?:same|normal)\s+usability\b", text):
        return None
    return SemanticFrame(
        schema="usability_target",
        slots={
            "target": "usability_parity",
            "parity_with": "normal_chatbot",
            "not_required": ["architecture_parity", "transformer_internals"],
            "desired_focus": "chatbot_usability",
        },
        provenance=_provenance("usability_frame", pattern="same_usability"),
    )


def _focus_frame(act: DialogueActResult) -> SemanticFrame | None:
    meaning = act.meaning
    if act.act != "strategic_redirect" and not meaning.get("new_focus"):
        return None
    deprioritize = meaning.get("deprioritize", [])
    if isinstance(deprioritize, str):
        deprioritize = [deprioritize]
    return SemanticFrame(
        schema="focus_shift",
        slots={
            "deprioritize": deprioritize,
            "new_focus": meaning.get("new_focus", "chatbot_language_layer"),
            "reason": meaning.get("reason", "user_priority_shift"),
            "desired_focus": meaning.get("new_focus", "chatbot_language_layer"),
        },
        provenance=_provenance("focus_frame", pattern="reasoning_engine_solid"),
    )


def compile_semantic_frames(
    utterance: NormalizedUtterance,
    act: DialogueActResult,
) -> tuple[list[SemanticFrame], list[str], list[str]]:
    text = utterance.clean
    known_topics, unknown = _topic_hits(text)

    frames: list[SemanticFrame] = []
    for builder in (
        lambda: _emotion_frame(utterance, act),
        lambda: _claim_frame(text, act),
        lambda: _architecture_frame(text),
        lambda: _scope_frame(act),
        lambda: _usability_frame(text),
        lambda: _focus_frame(act),
    ):
        frame = builder()
        if frame is not None:
            frames.append(frame)

    return frames, known_topics, unknown


def infer_topic(known_topics: list[str], act: DialogueActResult, fallback: str) -> str:
    if known_topics:
        priority = [
            "language_compiler",
            "chatbot",
            "usability",
            "reasoning_engine",
            "transformer",
            "ts_native",
        ]
        for topic in priority:
            if topic in known_topics:
                return topic.replace("_", " ")
    if act.meaning.get("new_focus"):
        return str(act.meaning["new_focus"]).replace("_", " ")
    if act.meaning.get("desired_focus"):
        return str(act.meaning["desired_focus"])
    return fallback