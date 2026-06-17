"""Build explicit TS meaning graphs from compiled frames and acts."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import Any

from ts_lang.graph_rules import apply_graph_derivations
from ts_lang.resources import graph_rules
from ts_lang.types import DialogueActResult, SemanticFrame

_DERIVED_NODE_KINDS = frozenset(
    {"rejected_scope", "accepted_scope", "constraint", "focus_target"}
)


@dataclass(frozen=True)
class MeaningNode:
    node_id: str
    kind: str
    label: str
    slots: dict[str, Any]
    provenance: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "kind": self.kind,
            "label": self.label,
            "slots": self.slots,
            "provenance": self.provenance,
        }


@dataclass(frozen=True)
class MeaningEdge:
    edge_id: str
    source_id: str
    target_id: str
    relation: str
    provenance: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation,
            "provenance": self.provenance,
        }


@dataclass(frozen=True)
class GraphValidationReport:
    valid: bool
    errors: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"valid": self.valid, "errors": list(self.errors)}


@dataclass(frozen=True)
class MeaningGraph:
    nodes: list[MeaningNode]
    edges: list[MeaningEdge]
    root_node_id: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "root_node_id": self.root_node_id,
            "summary": self.summary,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "validation": validate_meaning_graph(self).to_dict(),
        }

    def desired_focus(self) -> str | None:
        for node in self.nodes:
            if node.kind in {"scope_correction", "focus_shift", "usability_target"}:
                focus = node.slots.get("desired_focus") or node.slots.get("new_focus")
                if focus:
                    return str(focus)
            if node.kind == "claim" and node.slots.get("subject"):
                subj = node.slots["subject"]
                if subj not in {"TS chatbot", "conversation"}:
                    return str(subj)
        return None


def semantic_slug(value: Any) -> str:
    text = str(value).strip().lower()
    text = re.sub(r"[^\w]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "unknown"


def is_python_repr_string(value: str) -> bool:
    text = value.strip()
    if not text:
        return False
    if not ((text.startswith("[") and text.endswith("]")) or (text.startswith("(") and text.endswith(")"))):
        return False
    try:
        ast.literal_eval(text)
    except (SyntaxError, ValueError):
        return False
    return True


def _frame_provenance(frame: SemanticFrame) -> dict[str, Any]:
    return frame.provenance or {
        "source_type": "semantic_frame",
        "source_id": frame.schema,
        "schema": frame.schema,
    }


def _frame_node_id(frame: SemanticFrame) -> str:
    prov = _frame_provenance(frame)
    builder = prov.get("source_id", frame.schema)
    return f"node_frame_{semantic_slug(frame.schema)}_{semantic_slug(builder)}"


def _derived_node_id(kind: str, value: Any, *, polarity: str | None = None) -> str:
    if polarity:
        return f"node_{semantic_slug(kind)}_{semantic_slug(polarity)}_{semantic_slug(value)}"
    return f"node_{semantic_slug(kind)}_{semantic_slug(value)}"


def _edge_id(source_id: str, relation: str, target_id: str) -> str:
    return f"edge_{semantic_slug(source_id)}_{semantic_slug(relation)}_{semantic_slug(target_id)}"


def validate_meaning_graph(graph: MeaningGraph) -> GraphValidationReport:
    errors: list[str] = []
    node_ids = {node.node_id for node in graph.nodes}

    semantic_keys: dict[tuple[str, str], str] = {}
    for node in graph.nodes:
        if not node.provenance:
            errors.append(f"node_missing_provenance:{node.node_id}")

        for field_name in ("label",):
            if is_python_repr_string(str(node.label)):
                errors.append(f"python_repr_label:{node.node_id}:{node.label}")

        for slot_key, slot_value in node.slots.items():
            if isinstance(slot_value, str) and is_python_repr_string(slot_value):
                errors.append(f"python_repr_slot:{node.node_id}:{slot_key}:{slot_value}")
            if isinstance(slot_value, list):
                for item in slot_value:
                    if isinstance(item, str) and is_python_repr_string(item):
                        errors.append(f"python_repr_slot_item:{node.node_id}:{slot_key}:{item}")

        if node.kind in _DERIVED_NODE_KINDS:
            semantic_value = str(node.slots.get("value", node.label))
            polarity = node.slots.get("polarity")
            semantic_key = (
                node.kind,
                str(polarity) if polarity is not None else "",
                semantic_slug(semantic_value),
            )
            if semantic_key in semantic_keys and semantic_keys[semantic_key] != node.node_id:
                errors.append(
                    f"duplicate_semantic_node:{node.kind}:{semantic_value}:"
                    f"{semantic_keys[semantic_key]} vs {node.node_id}"
                )
            else:
                semantic_keys[semantic_key] = node.node_id

    for edge in graph.edges:
        if not edge.provenance:
            errors.append(f"edge_missing_provenance:{edge.edge_id}")
        if edge.source_id not in node_ids:
            errors.append(f"edge_missing_source:{edge.edge_id}:{edge.source_id}")
        if edge.target_id not in node_ids:
            errors.append(f"edge_missing_target:{edge.edge_id}:{edge.target_id}")

    return GraphValidationReport(valid=not errors, errors=tuple(errors))


class _GraphBuilder:
    def __init__(self) -> None:
        self.nodes: list[MeaningNode] = []
        self.edges: list[MeaningEdge] = []
        self._node_ids: set[str] = set()
        self._semantic_nodes: dict[tuple[str, str], str] = {}
        self._edge_ids: set[str] = set()

    def add_node(self, node: MeaningNode) -> str:
        if node.node_id not in self._node_ids:
            self.nodes.append(node)
            self._node_ids.add(node.node_id)
        return node.node_id

    def add_derived_node(
        self,
        *,
        kind: str,
        value: Any,
        label: str | None = None,
        slots: dict[str, Any] | None = None,
        provenance: dict[str, Any],
        polarity: str | None = None,
    ) -> str:
        semantic_value = str(value)
        semantic_key = (kind, polarity or "", semantic_slug(semantic_value))
        if semantic_key in self._semantic_nodes:
            return self._semantic_nodes[semantic_key]

        node_id = _derived_node_id(kind, semantic_value, polarity=polarity)
        node = MeaningNode(
            node_id=node_id,
            kind=kind,
            label=label or semantic_value,
            slots=slots or {"value": semantic_value},
            provenance=provenance,
        )
        self._semantic_nodes[semantic_key] = node_id
        return self.add_node(node)

    def add_edge(
        self,
        *,
        source_id: str,
        target_id: str,
        relation: str,
        provenance: dict[str, Any],
    ) -> None:
        edge_id = _edge_id(source_id, relation, target_id)
        if edge_id in self._edge_ids:
            return
        self.edges.append(
            MeaningEdge(
                edge_id=edge_id,
                source_id=source_id,
                target_id=target_id,
                relation=relation,
                provenance=provenance,
            )
        )
        self._edge_ids.add(edge_id)


def build_meaning_graph(
    *,
    dialogue_act: str,
    subact: str | None,
    act_result: DialogueActResult,
    frames: list[SemanticFrame],
    topic: str,
) -> MeaningGraph:
    builder = _GraphBuilder()

    act_provenance = {
        "source_type": "dialogue_act",
        "source_id": dialogue_act,
        "subact": subact,
        "matched_phrases": act_result.meaning.get("matched_phrases", []),
        "confidence": act_result.confidence,
    }
    root_id = builder.add_node(
        MeaningNode(
            node_id="node_act_root",
            kind="dialogue_act",
            label=dialogue_act,
            slots={"subact": subact, "topic": topic, "meaning": act_result.meaning},
            provenance=act_provenance,
        )
    )

    for frame in frames:
        prov = _frame_provenance(frame)
        frame_node_id = builder.add_node(
            MeaningNode(
                node_id=_frame_node_id(frame),
                kind=frame.schema,
                label=frame.schema.replace("_", " "),
                slots=dict(frame.slots),
                provenance=prov,
            )
        )
        builder.add_edge(
            source_id=root_id,
            target_id=frame_node_id,
            relation="expresses",
            provenance={
                "source_type": "frame_link",
                "source_id": prov["source_id"],
                "schema": frame.schema,
            },
        )

        apply_graph_derivations(
            builder,
            frame=frame,
            frame_node_id=frame_node_id,
            frame_provenance=prov,
            rules=graph_rules(),
        )

    derived_count = sum(1 for node in builder.nodes if node.kind in _DERIVED_NODE_KINDS)
    summary = (
        f"{dialogue_act} over {topic} with {len(frames)} frame(s) "
        f"and {derived_count} derived node(s)"
    )
    graph = MeaningGraph(
        nodes=builder.nodes,
        edges=builder.edges,
        root_node_id=root_id,
        summary=summary,
    )
    report = validate_meaning_graph(graph)
    if not report.valid:
        raise ValueError(f"Invalid meaning graph: {', '.join(report.errors)}")
    return graph