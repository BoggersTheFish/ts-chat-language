"""Declarative semantic frame rule engine."""

from __future__ import annotations

import re
from typing import Any

from ts_lang.slot_normalize import extend_slot_values, normalize_frame_slots
from ts_lang.types import DialogueActResult, NormalizedUtterance, SemanticFrame

_LIST_MERGE_SLOTS = frozenset(
    {"avoid", "prefer", "rejects", "accepts", "deprioritize", "not_required"}
)


def _match_condition(
    when: dict[str, Any],
    *,
    text: str,
    act: DialogueActResult,
    utterance: NormalizedUtterance,
) -> bool:
    if "all" in when:
        return all(
            _match_condition(item, text=text, act=act, utterance=utterance)
            for item in when["all"]
        )
    if "any" in when:
        return any(
            _match_condition(item, text=text, act=act, utterance=utterance)
            for item in when["any"]
        )
    if "text_regex" in when:
        return bool(re.search(str(when["text_regex"]), text, re.IGNORECASE))
    if "act_in" in when:
        return act.act in when["act_in"]
    if "act_meaning_has" in when:
        return when["act_meaning_has"] in act.meaning
    if "emotion_present" in when:
        return bool(when["emotion_present"]) == bool(act.emotion)
    if "markers" in when:
        marker_name = str(when["markers"])
        return bool(getattr(utterance.markers, marker_name, False))
    return True


def _first_meaning_value(meaning: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if key in meaning and meaning[key] not in (None, "", []):
            return meaning[key]
    return None


def _build_slots(emit: dict[str, Any], *, act: DialogueActResult, utterance: NormalizedUtterance) -> dict[str, Any]:
    slots: dict[str, Any] = dict(emit.get("slots", {}))

    for slot, key in emit.get("slots_from_meaning", {}).items():
        if key in act.meaning:
            slots[slot] = act.meaning[key]

    for slot, key in emit.get("slots_from_emotion", {}).items():
        if key in act.emotion:
            slots[slot] = act.emotion[key]

    for slot, key in emit.get("slots_from_markers", {}).items():
        value = getattr(utterance.markers, key, None)
        if value is not None and slot not in slots:
            slots[slot] = value

    for slot, default in emit.get("slot_defaults", {}).items():
        slots.setdefault(slot, default)

    for slot, keys in emit.get("slots_merge_from_meaning", {}).items():
        values: list[str] = []
        if isinstance(slots.get(slot), list):
            extend_slot_values(values, slots[slot])
        elif slot in slots:
            extend_slot_values(values, slots[slot])
        for key in keys:
            if key in act.meaning:
                extend_slot_values(values, act.meaning[key])
        if values:
            slots[slot] = values

    for slot, values in emit.get("slot_append", {}).items():
        current: list[str] = []
        extend_slot_values(current, slots.get(slot, []))
        extend_slot_values(current, values)
        slots[slot] = current

    focus_keys = emit.get("desired_focus_from_meaning", [])
    if focus_keys:
        focus = _first_meaning_value(act.meaning, list(focus_keys))
        if focus is not None:
            slots["desired_focus"] = focus

    if slots.get("subject") == "conversation" and act.meaning.get("desired_focus"):
        slots["subject"] = act.meaning["desired_focus"]

    if emit.get("schema") == "emotion_frame" and "intensity" not in slots:
        slots["intensity"] = utterance.markers.intensity

    return slots


def _provenance_for_rule(rule_id: str, emit: dict[str, Any]) -> dict[str, Any]:
    prov = dict(emit.get("provenance", {}))
    prov.setdefault("source_type", "frame_rule")
    prov.setdefault("source_id", rule_id)
    prov.setdefault("rule_id", rule_id)
    return prov


def _emit_frame(
    rule: dict[str, Any],
    *,
    act: DialogueActResult,
    utterance: NormalizedUtterance,
) -> SemanticFrame | None:
    emit = rule.get("emit", {})
    schema = emit.get("schema")
    if not schema:
        return None
    slots = _build_slots(emit, act=act, utterance=utterance)
    if schema == "scope_correction" and not slots.get("rejects") and not slots.get("accepts"):
        return None
    if schema == "architecture_preference" and not slots.get("avoid") and not slots.get("prefer"):
        return None
    return SemanticFrame(
        schema=schema,
        slots=slots,
        provenance=_provenance_for_rule(str(rule["id"]), emit),
    )


def _merge_frames(frames: list[SemanticFrame]) -> list[SemanticFrame]:
    merged: dict[str, SemanticFrame] = {}
    order: list[str] = []

    for frame in frames:
        if frame.schema not in merged:
            merged[frame.schema] = frame
            order.append(frame.schema)
            continue

        existing = merged[frame.schema]
        slots = dict(existing.slots)
        for key, value in frame.slots.items():
            if key in _LIST_MERGE_SLOTS:
                combined: list[str] = []
                extend_slot_values(combined, slots.get(key, []))
                extend_slot_values(combined, value)
                slots[key] = combined
            elif key == "desired_focus" and value:
                slots[key] = value
            elif key not in slots or not slots[key]:
                slots[key] = value
        merged[frame.schema] = SemanticFrame(
            schema=frame.schema,
            slots=slots,
            provenance=existing.provenance,
        )

    return [merged[schema] for schema in order]


def evaluate_frame_rules(
    rules: list[dict[str, Any]],
    utterance: NormalizedUtterance,
    act: DialogueActResult,
) -> tuple[list[SemanticFrame], list[str]]:
    text = utterance.clean
    sorted_rules = sorted(rules, key=lambda rule: (-int(rule.get("priority", 0)), str(rule["id"])))
    fired: list[str] = []
    frames: list[SemanticFrame] = []

    for rule in sorted_rules:
        when = rule.get("when", {})
        if not _match_condition(when, text=text, act=act, utterance=utterance):
            continue
        frame = _emit_frame(rule, act=act, utterance=utterance)
        if frame is None:
            continue
        fired.append(str(rule["id"]))
        frames.append(frame)

    coalesced = _merge_frames(frames)
    normalized = [normalize_frame_slots(frame) for frame in coalesced]
    return normalized, fired