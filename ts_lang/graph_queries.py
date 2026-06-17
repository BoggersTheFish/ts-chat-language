"""Query helpers for graph-driven state and planning."""

from __future__ import annotations

from typing import Any

from ts_lang.meaning_graph import MeaningGraph, MeaningNode

_ACCEPTABLE_FRAME_KINDS = frozenset(
    {"scope_correction", "focus_shift", "usability_target", "claim"}
)
_MAIN_POINT_PRIORITY = (
    "usability_target",
    "scope_correction",
    "focus_shift",
    "claim",
    "architecture_preference",
)


def nodes_of_kind(graph: MeaningGraph, kind: str) -> list[MeaningNode]:
    return [node for node in graph.nodes if node.kind == kind]


def first_of_kind(graph: MeaningGraph, kind: str) -> MeaningNode | None:
    matches = nodes_of_kind(graph, kind)
    return matches[0] if matches else None


def derived_values(graph: MeaningGraph, kind: str) -> list[str]:
    values: list[str] = []
    for node in nodes_of_kind(graph, kind):
        value = str(node.slots.get("value", node.label))
        if value not in values:
            values.append(value)
    return values


def rejected_scopes(graph: MeaningGraph) -> list[str]:
    return derived_values(graph, "rejected_scope")


def accepted_scopes(graph: MeaningGraph) -> list[str]:
    return derived_values(graph, "accepted_scope")


def preferred_constraints(graph: MeaningGraph) -> list[str]:
    values: list[str] = []
    for node in nodes_of_kind(graph, "constraint"):
        if node.slots.get("polarity") != "prefer":
            continue
        value = str(node.slots.get("value", node.label))
        if value not in values:
            values.append(value)
    return values


def emotion_affect(graph: MeaningGraph) -> str | None:
    node = first_of_kind(graph, "emotion_frame")
    if node is None:
        return None
    affect = node.slots.get("affect")
    return str(affect) if affect else None


def acceptable_frame_nodes(graph: MeaningGraph) -> list[MeaningNode]:
    return [node for node in graph.nodes if node.kind in _ACCEPTABLE_FRAME_KINDS]


def has_frame_kind(graph: MeaningGraph, kind: str) -> bool:
    return first_of_kind(graph, kind) is not None


def scope_correction_focus(graph: MeaningGraph) -> str | None:
    node = first_of_kind(graph, "scope_correction")
    if node is None:
        return None
    focus = node.slots.get("desired_focus")
    if focus:
        return str(focus)
    accepts = node.slots.get("accepts", [])
    if accepts:
        return str(accepts[0])
    accepted = accepted_scopes(graph)
    return accepted[0] if accepted else None


def scope_correction_rejects(graph: MeaningGraph) -> list[str]:
    node = first_of_kind(graph, "scope_correction")
    rejects = list(rejected_scopes(graph))
    if node is not None:
        for item in node.slots.get("rejects", []):
            text = str(item)
            if text not in rejects:
                rejects.append(text)
    return rejects


def main_point_frame_node(graph: MeaningGraph) -> MeaningNode | None:
    for kind in _MAIN_POINT_PRIORITY:
        node = first_of_kind(graph, kind)
        if node is not None:
            return node
    return None