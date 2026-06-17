"""Build explicit TS meaning graphs from compiled frames and acts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ts_lang.types import DialogueActResult, SemanticFrame


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


def _frame_provenance(frame: SemanticFrame, index: int) -> dict[str, Any]:
    return frame.provenance or {
        "source_type": "semantic_frame",
        "source_id": f"frame_{index:02d}",
        "schema": frame.schema,
    }


def build_meaning_graph(
    *,
    dialogue_act: str,
    subact: str | None,
    act_result: DialogueActResult,
    frames: list[SemanticFrame],
    topic: str,
) -> MeaningGraph:
    nodes: list[MeaningNode] = []
    edges: list[MeaningEdge] = []
    edge_counter = 0

    act_provenance = {
        "source_type": "dialogue_act",
        "source_id": dialogue_act,
        "subact": subact,
        "matched_phrases": act_result.meaning.get("matched_phrases", []),
        "confidence": act_result.confidence,
    }
    root = MeaningNode(
        node_id="node_act_root",
        kind="dialogue_act",
        label=dialogue_act,
        slots={"subact": subact, "topic": topic, "meaning": act_result.meaning},
        provenance=act_provenance,
    )
    nodes.append(root)

    for index, frame in enumerate(frames):
        prov = _frame_provenance(frame, index)
        node_id = f"node_frame_{index:02d}_{frame.schema}"
        node = MeaningNode(
            node_id=node_id,
            kind=frame.schema,
            label=frame.schema.replace("_", " "),
            slots=dict(frame.slots),
            provenance=prov,
        )
        nodes.append(node)
        edge_counter += 1
        edges.append(
            MeaningEdge(
                edge_id=f"edge_{edge_counter:03d}",
                source_id=root.node_id,
                target_id=node_id,
                relation="expresses",
                provenance={
                    "source_type": "frame_link",
                    "source_id": prov["source_id"],
                    "schema": frame.schema,
                },
            )
        )

        if frame.schema == "scope_correction":
            for reject in frame.slots.get("rejects", []):
                reject_id = f"node_reject_{index}_{reject}"
                nodes.append(
                    MeaningNode(
                        node_id=reject_id,
                        kind="rejected_scope",
                        label=str(reject),
                        slots={"value": reject},
                        provenance={**prov, "derived_from": "scope_correction.rejects"},
                    )
                )
                edge_counter += 1
                edges.append(
                    MeaningEdge(
                        edge_id=f"edge_{edge_counter:03d}",
                        source_id=node_id,
                        target_id=reject_id,
                        relation="rejects",
                        provenance={"source_type": "scope_correction", "slot": "rejects"},
                    )
                )
            for accept in frame.slots.get("accepts", []):
                accept_id = f"node_accept_{index}_{accept}"
                nodes.append(
                    MeaningNode(
                        node_id=accept_id,
                        kind="accepted_scope",
                        label=str(accept),
                        slots={"value": accept},
                        provenance={**prov, "derived_from": "scope_correction.accepts"},
                    )
                )
                edge_counter += 1
                edges.append(
                    MeaningEdge(
                        edge_id=f"edge_{edge_counter:03d}",
                        source_id=node_id,
                        target_id=accept_id,
                        relation="accepts",
                        provenance={"source_type": "scope_correction", "slot": "accepts"},
                    )
                )

        if frame.schema == "architecture_preference":
            for avoid in frame.slots.get("avoid", []):
                avoid_id = f"node_avoid_{index}_{avoid}"
                nodes.append(
                    MeaningNode(
                        node_id=avoid_id,
                        kind="constraint",
                        label=str(avoid),
                        slots={"polarity": "avoid", "value": avoid},
                        provenance={**prov, "derived_from": "architecture_preference.avoid"},
                    )
                )
                edge_counter += 1
                edges.append(
                    MeaningEdge(
                        edge_id=f"edge_{edge_counter:03d}",
                        source_id=node_id,
                        target_id=avoid_id,
                        relation="avoids",
                        provenance={"source_type": "architecture_preference", "slot": "avoid"},
                    )
                )
            for prefer in frame.slots.get("prefer", []):
                prefer_id = f"node_prefer_{index}_{prefer}"
                nodes.append(
                    MeaningNode(
                        node_id=prefer_id,
                        kind="constraint",
                        label=str(prefer),
                        slots={"polarity": "prefer", "value": prefer},
                        provenance={**prov, "derived_from": "architecture_preference.prefer"},
                    )
                )
                edge_counter += 1
                edges.append(
                    MeaningEdge(
                        edge_id=f"edge_{edge_counter:03d}",
                        source_id=node_id,
                        target_id=prefer_id,
                        relation="prefers",
                        provenance={"source_type": "architecture_preference", "slot": "prefer"},
                    )
                )

        if frame.schema == "focus_shift":
            new_focus = frame.slots.get("new_focus")
            if new_focus:
                focus_id = f"node_focus_{index}_{new_focus}"
                nodes.append(
                    MeaningNode(
                        node_id=focus_id,
                        kind="focus_target",
                        label=str(new_focus),
                        slots={"new_focus": new_focus},
                        provenance={**prov, "derived_from": "focus_shift.new_focus"},
                    )
                )
                edge_counter += 1
                edges.append(
                    MeaningEdge(
                        edge_id=f"edge_{edge_counter:03d}",
                        source_id=node_id,
                        target_id=focus_id,
                        relation="shifts_to",
                        provenance={"source_type": "focus_shift", "slot": "new_focus"},
                    )
                )

    summary = f"{dialogue_act} over {topic} with {len(frames)} frame(s) and {len(nodes) - 1} derived node(s)"
    return MeaningGraph(
        nodes=nodes,
        edges=edges,
        root_node_id=root.node_id,
        summary=summary,
    )