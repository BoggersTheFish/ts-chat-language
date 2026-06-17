"""Aggregate graph-diff history for memory-aware response planning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ts_state.conversation import ConversationState


def _humanize(value: str) -> str:
    return value.replace("_", " ")


def _extend_unique(target: list[str], values: Any) -> None:
    if not values:
        return
    if isinstance(values, str):
        values = [values]
    for value in values:
        text = str(value)
        if text and text not in target:
            target.append(text)


@dataclass(frozen=True)
class DiffMemory:
    prior_turn_count: int
    prior_rejects: tuple[str, ...]
    prior_accepts: tuple[str, ...]
    focus_trajectory: tuple[str, ...]
    current_focus_shift: dict[str, str | None]
    memory_context: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "prior_turn_count": self.prior_turn_count,
            "prior_rejects": list(self.prior_rejects),
            "prior_accepts": list(self.prior_accepts),
            "focus_trajectory": list(self.focus_trajectory),
            "current_focus_shift": self.current_focus_shift,
            "memory_context": self.memory_context,
            "summary": self.summary,
        }


def _accumulate_diff(
    diff: dict[str, Any],
    *,
    rejects: list[str],
    accepts: list[str],
    focus_trajectory: list[str],
) -> None:
    _extend_unique(rejects, diff.get("rejects_added", []))
    _extend_unique(accepts, diff.get("accepts_added", []))
    focus_change = diff.get("focus_change", {})
    current_focus = focus_change.get("current")
    if current_focus and (not focus_trajectory or focus_trajectory[-1] != current_focus):
        focus_trajectory.append(str(current_focus))


def _build_memory_context(
    *,
    prior_rejects: list[str],
    focus_trajectory: list[str],
    current_focus_shift: dict[str, str | None],
    dialogue_act: str,
) -> str:
    if not prior_rejects and not focus_trajectory and not current_focus_shift.get("current"):
        return ""

    parts: list[str] = []

    if prior_rejects:
        labels = [_humanize(item) for item in prior_rejects[:4]]
        parts.append(f"You already ruled out {', '.join(labels)}")

    previous_focus = current_focus_shift.get("previous")
    current_focus = current_focus_shift.get("current")
    if (
        dialogue_act in {"strategic_redirect", "correct_assistant", "confirm_direction"}
        and previous_focus
        and current_focus
        and previous_focus != current_focus
    ):
        parts.append(
            f"shifting focus from {_humanize(previous_focus)} to {_humanize(current_focus)}"
        )
    elif len(focus_trajectory) >= 2 and dialogue_act in {"ask_for_next_step", "request_plan"}:
        parts.append(
            "focus moved from "
            f"{_humanize(focus_trajectory[-2])} to {_humanize(focus_trajectory[-1])}"
        )

    if not parts:
        return ""

    if len(parts) == 1:
        return f"{parts[0]}."
    return f"{parts[0]}; {parts[1]}."


def build_diff_memory(state: ConversationState, *, dialogue_act: str) -> DiffMemory:
    prior_rejects: list[str] = []
    prior_accepts: list[str] = []
    focus_trajectory: list[str] = []

    for record in state.turn_history:
        _accumulate_diff(
            record.graph_diff or {},
            rejects=prior_rejects,
            accepts=prior_accepts,
            focus_trajectory=focus_trajectory,
        )

    current_diff = state.last_graph_diff or {}
    current_focus_shift = dict(current_diff.get("focus_change", {}))

    memory_context = _build_memory_context(
        prior_rejects=prior_rejects,
        focus_trajectory=focus_trajectory,
        current_focus_shift=current_focus_shift,
        dialogue_act=dialogue_act,
    )

    summary_parts = [f"prior_turns={len(state.turn_history)}"]
    if prior_rejects:
        summary_parts.append(f"prior_rejects={','.join(prior_rejects)}")
    if current_focus_shift.get("current"):
        summary_parts.append(f"focus={current_focus_shift.get('current')}")
    if memory_context:
        summary_parts.append("memory_context=set")

    return DiffMemory(
        prior_turn_count=len(state.turn_history),
        prior_rejects=tuple(prior_rejects),
        prior_accepts=tuple(prior_accepts),
        focus_trajectory=tuple(focus_trajectory),
        current_focus_shift=current_focus_shift,
        memory_context=memory_context,
        summary="; ".join(summary_parts),
    )