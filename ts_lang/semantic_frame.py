"""Semantic frame compiler from declarative pack rules."""

from __future__ import annotations

from ts_lang.frame_rules import evaluate_frame_rules
from ts_lang.resources import lexicon, semantic_rules, topic_rules
from ts_lang.topic_rules import infer_topic_from_rules
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


def compile_semantic_frames(
    utterance: NormalizedUtterance,
    act: DialogueActResult,
) -> tuple[list[SemanticFrame], list[str], list[str]]:
    text = utterance.clean
    known_topics, unknown = _topic_hits(text)
    frames, _fired = evaluate_frame_rules(semantic_rules(), utterance, act)
    return frames, known_topics, unknown


def last_fired_rule_ids(
    utterance: NormalizedUtterance,
    act: DialogueActResult,
) -> list[str]:
    _frames, fired = evaluate_frame_rules(semantic_rules(), utterance, act)
    return fired


def infer_topic(known_topics: list[str], act: DialogueActResult, fallback: str) -> str:
    topic, _fired = infer_topic_from_rules(known_topics, act, fallback, topic_rules())
    return topic