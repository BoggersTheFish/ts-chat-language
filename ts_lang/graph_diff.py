"""Diff meaning graphs across turns for multi-turn memory receipts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ts_lang.graph_queries import (
    accepted_scopes,
    avoided_constraints,
    preferred_constraints,
    rejected_scopes,
)
from ts_lang.meaning_graph import MeaningGraph, MeaningNode, semantic_slug

_DERIVED_NODE_KINDS = frozenset(
    {"rejected_scope", "accepted_scope", "constraint", "focus_target"}
)
_DIFFABLE_FRAME_KINDS = frozenset(
    {
        "emotion_frame",
        "claim",
        "architecture_preference",
        "scope_correction",
        "usability_target",
        "focus_shift",
    }
)


@dataclass(frozen=True)
class SemanticNodeSnapshot:
    semantic_key: str
    node_id: str
    kind: str
    label: str
    value: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "semantic_key": self.semantic_key,
            "node_id": self.node_id,
            "kind": self.kind,
            "label": self.label,
            "value": self.value,
        }


@dataclass(frozen=True)
class GraphDiff:
    previous_turn_id: int | None
    current_turn_id: int
    dialogue_act_change: dict[str, str | None]
    topic_change: dict[str, str | None]
    focus_change: dict[str, str | None]
    added_nodes: tuple[SemanticNodeSnapshot, ...]
    removed_nodes: tuple[SemanticNodeSnapshot, ...]
    rejects_added: tuple[str, ...]
    rejects_removed: tuple[str, ...]
    accepts_added: tuple[str, ...]
    accepts_removed: tuple[str, ...]
    prefers_added: tuple[str, ...]
    prefers_removed: tuple[str, ...]
    avoids_added: tuple[str, ...]
    avoids_removed: tuple[str, ...]
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "previous_turn_id": self.previous_turn_id,
            "current_turn_id": self.current_turn_id,
            "dialogue_act_change": self.dialogue_act_change,
            "topic_change": self.topic_change,
            "focus_change": self.focus_change,
            "added_nodes": [node.to_dict() for node in self.added_nodes],
            "removed_nodes": [node.to_dict() for node in self.removed_nodes],
            "rejects_added": list(self.rejects_added),
            "rejects_removed": list(self.rejects_removed),
            "accepts_added": list(self.accepts_added),
            "accepts_removed": list(self.accepts_removed),
            "prefers_added": list(self.prefers_added),
            "prefers_removed": list(self.prefers_removed),
            "avoids_added": list(self.avoids_added),
            "avoids_removed": list(self.avoids_removed),
            "summary": self.summary,
        }


def semantic_node_key(node: MeaningNode) -> str:
    if node.kind == "dialogue_act":
        return f"dialogue_act:{semantic_slug(node.label)}"
    if node.kind in _DERIVED_NODE_KINDS:
        polarity = str(node.slots.get("polarity", ""))
        value = str(node.slots.get("value", node.label))
        return f"{node.kind}:{polarity}:{semantic_slug(value)}"
    if node.kind in _DIFFABLE_FRAME_KINDS:
        return f"frame:{node.kind}:{node.node_id}"
    return f"node:{node.kind}:{node.node_id}"


def _snapshot(node: MeaningNode) -> SemanticNodeSnapshot:
    value = node.slots.get("value")
    if value is None and node.kind == "focus_target":
        value = node.slots.get("new_focus")
    return SemanticNodeSnapshot(
        semantic_key=semantic_node_key(node),
        node_id=node.node_id,
        kind=node.kind,
        label=node.label,
        value=str(value) if value is not None else None,
    )


def _diffable_nodes(graph: MeaningGraph) -> dict[str, SemanticNodeSnapshot]:
    indexed: dict[str, SemanticNodeSnapshot] = {}
    for node in graph.nodes:
        if node.kind == "dialogue_act":
            continue
        snap = _snapshot(node)
        indexed[snap.semantic_key] = snap
    return indexed


def _root_topic(graph: MeaningGraph) -> str | None:
    for node in graph.nodes:
        if node.kind == "dialogue_act":
            topic = node.slots.get("topic")
            return str(topic) if topic else None
    return None


def _root_dialogue_act(graph: MeaningGraph) -> str | None:
    for node in graph.nodes:
        if node.kind == "dialogue_act":
            return node.label
    return None


def _list_delta(previous: list[str], current: list[str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    prev_set = set(previous)
    curr_set = set(current)
    added = tuple(item for item in current if item not in prev_set)
    removed = tuple(item for item in previous if item not in curr_set)
    return added, removed


def _build_summary(
    *,
    current_turn_id: int,
    dialogue_act_change: dict[str, str | None],
    topic_change: dict[str, str | None],
    focus_change: dict[str, str | None],
    added_nodes: tuple[SemanticNodeSnapshot, ...],
    removed_nodes: tuple[SemanticNodeSnapshot, ...],
    rejects_added: tuple[str, ...],
    accepts_added: tuple[str, ...],
) -> str:
    parts: list[str] = [f"turn {current_turn_id}"]

    prev_act = dialogue_act_change.get("previous")
    curr_act = dialogue_act_change.get("current")
    if prev_act != curr_act and curr_act:
        parts.append(f"act {prev_act or 'none'} -> {curr_act}")

    prev_topic = topic_change.get("previous")
    curr_topic = topic_change.get("current")
    if prev_topic != curr_topic and curr_topic:
        parts.append(f"topic {prev_topic or 'none'} -> {curr_topic}")

    prev_focus = focus_change.get("previous")
    curr_focus = focus_change.get("current")
    if prev_focus != curr_focus and curr_focus:
        parts.append(f"focus {prev_focus or 'none'} -> {curr_focus}")

    if rejects_added:
        parts.append(f"+rejects:{','.join(rejects_added)}")
    if accepts_added:
        parts.append(f"+accepts:{','.join(accepts_added)}")
    if added_nodes:
        kinds = ",".join(sorted({node.kind for node in added_nodes}))
        parts.append(f"+nodes:{kinds}")
    if removed_nodes:
        kinds = ",".join(sorted({node.kind for node in removed_nodes}))
        parts.append(f"-nodes:{kinds}")

    return "; ".join(parts)


def diff_meaning_graphs(
    previous: MeaningGraph | None,
    current: MeaningGraph,
    *,
    previous_turn_id: int | None,
    current_turn_id: int,
) -> GraphDiff:
    prev_nodes = _diffable_nodes(previous) if previous is not None else {}
    curr_nodes = _diffable_nodes(current)

    added_keys = [key for key in curr_nodes if key not in prev_nodes]
    removed_keys = [key for key in prev_nodes if key not in curr_nodes]

    added_nodes = tuple(curr_nodes[key] for key in sorted(added_keys))
    removed_nodes = tuple(prev_nodes[key] for key in sorted(removed_keys))

    prev_focus = previous.desired_focus() if previous is not None else None
    curr_focus = current.desired_focus()

    prev_rejects = rejected_scopes(previous) if previous is not None else []
    curr_rejects = rejected_scopes(current)
    rejects_added, rejects_removed = _list_delta(prev_rejects, curr_rejects)

    prev_accepts = accepted_scopes(previous) if previous is not None else []
    curr_accepts = accepted_scopes(current)
    accepts_added, accepts_removed = _list_delta(prev_accepts, curr_accepts)

    prev_prefers = preferred_constraints(previous) if previous is not None else []
    curr_prefers = preferred_constraints(current)
    prefers_added, prefers_removed = _list_delta(prev_prefers, curr_prefers)

    prev_avoids = avoided_constraints(previous) if previous is not None else []
    curr_avoids = avoided_constraints(current)
    avoids_added, avoids_removed = _list_delta(prev_avoids, curr_avoids)

    dialogue_act_change = {
        "previous": _root_dialogue_act(previous) if previous is not None else None,
        "current": _root_dialogue_act(current),
    }
    topic_change = {
        "previous": _root_topic(previous) if previous is not None else None,
        "current": _root_topic(current),
    }
    focus_change = {
        "previous": prev_focus,
        "current": curr_focus,
    }

    summary = _build_summary(
        current_turn_id=current_turn_id,
        dialogue_act_change=dialogue_act_change,
        topic_change=topic_change,
        focus_change=focus_change,
        added_nodes=added_nodes,
        removed_nodes=removed_nodes,
        rejects_added=rejects_added,
        accepts_added=accepts_added,
    )

    return GraphDiff(
        previous_turn_id=previous_turn_id,
        current_turn_id=current_turn_id,
        dialogue_act_change=dialogue_act_change,
        topic_change=topic_change,
        focus_change=focus_change,
        added_nodes=added_nodes,
        removed_nodes=removed_nodes,
        rejects_added=rejects_added,
        rejects_removed=rejects_removed,
        accepts_added=accepts_added,
        accepts_removed=accepts_removed,
        prefers_added=prefers_added,
        prefers_removed=prefers_removed,
        avoids_added=avoids_added,
        avoids_removed=avoids_removed,
        summary=summary,
    )