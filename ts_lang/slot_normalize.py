"""Normalize list-valued semantic frame slots."""

from __future__ import annotations

from typing import Any

from ts_lang.types import SemanticFrame

_LIST_SLOT_KEYS: dict[str, tuple[str, ...]] = {
    "scope_correction": ("rejects", "accepts"),
    "architecture_preference": ("avoid", "prefer"),
    "focus_shift": ("deprioritize",),
    "usability_target": ("not_required",),
}


def append_unique_string(target: list[str], value: Any) -> None:
    text = str(value).strip()
    if text and text not in target:
        target.append(text)


def extend_slot_values(target: list[str], value: Any) -> None:
    if value is None:
        return
    if isinstance(value, list):
        for item in value:
            append_unique_string(target, item)
    else:
        append_unique_string(target, value)


def normalize_string_list(values: Any) -> list[str]:
    normalized: list[str] = []
    extend_slot_values(normalized, values)
    return normalized


def normalize_frame_slots(frame: SemanticFrame) -> SemanticFrame:
    slots = dict(frame.slots)
    for key in _LIST_SLOT_KEYS.get(frame.schema, ()):
        if key in slots:
            slots[key] = normalize_string_list(slots[key])
    return SemanticFrame(schema=frame.schema, slots=slots, provenance=frame.provenance)