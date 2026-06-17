"""Orchestrate normalize → dialogue act → semantic frame compilation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ts_lang.dialogue_act import compile_dialogue_act
from ts_lang.meaning_graph import build_meaning_graph
from ts_lang.normalize import normalize_utterance
from ts_lang.semantic_frame import compile_semantic_frames, infer_topic
from ts_lang.types import CompiledTurn

if TYPE_CHECKING:
    from ts_state.conversation import ConversationState

PARTIAL_PARSE_THRESHOLD = 0.45


def compile_utterance(raw: str, state: ConversationState | None = None) -> CompiledTurn:
    utterance = normalize_utterance(raw)
    current_topic = state.current_topic if state else "general conversation"
    rejected = state.rejected_frames if state else []

    act = compile_dialogue_act(
        utterance,
        current_topic=current_topic,
        rejected_frames=rejected,
    )
    frames, known_topics, unknown = compile_semantic_frames(utterance, act)
    topic = infer_topic(known_topics, act, current_topic)

    confidence = act.confidence
    ambiguities = list(act.ambiguities)
    status = "ok"
    repair_action = None

    if confidence < PARTIAL_PARSE_THRESHOLD or unknown:
        status = "partial_parse"
        repair_action = "ask_targeted_question"
        if unknown:
            ambiguities.extend(unknown)

    meaning_graph = build_meaning_graph(
        dialogue_act=act.act,
        subact=act.subact,
        act_result=act,
        frames=frames,
        topic=topic,
    )

    return CompiledTurn(
        raw=raw,
        normalized=utterance.clean,
        dialogue_act=act.act,
        subact=act.subact,
        semantic_frames=frames,
        meaning_graph=meaning_graph,
        emotion=dict(act.emotion),
        topic=topic,
        confidence=confidence,
        ambiguities=ambiguities,
        status=status,
        repair_action=repair_action,
        known_terms=known_topics,
        unknown_terms=unknown,
    )