"""Deterministic MeaningGraph to TS-Reasoner request bridge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ts_lang.meaning_graph import MeaningGraph, validate_meaning_graph
from ts_reasoner.structured_request import (
    Ambiguity, ProvenanceRecord, ReasoningRequest, StructuredClaim,
    StructuredConstraint, StructuredEntity, StructuredRelation,
)
from ts_reasoner.typed_support import canonical_hash


@dataclass(frozen=True)
class BridgeResult:
    status: str
    warnings: tuple[str, ...]
    request: ReasoningRequest


def bridge_meaning_graph(graph: MeaningGraph, original_text: str, *, memory_relations: Iterable[StructuredRelation] = (), memory_claims: Iterable[StructuredClaim] = (), memory_constraints: Iterable[StructuredConstraint] = (), repair_actions: tuple[str, ...] = (), habitat: dict | None = None) -> BridgeResult:
    warnings: list[str] = []
    relations = list(memory_relations); claims = list(memory_claims); constraints = list(memory_constraints)
    entities: dict[str, StructuredEntity] = {}
    ambiguities: list[Ambiguity] = []
    provenance: list[ProvenanceRecord] = []
    intent = "assert"
    validation = validate_meaning_graph(graph)
    if not validation.valid: warnings.extend(f"BLOCKING:{item}" for item in validation.errors)

    def entity(entity_id: str, text: str = "") -> None:
        if entity_id and entity_id not in entities: entities[entity_id] = StructuredEntity(entity_id, text or entity_id.replace("_", " "))

    for node in graph.nodes:
        prov = node.provenance
        provenance.append(ProvenanceRecord(f"prov:{node.node_id}", str(prov.get("source_type", "graph")), node.node_id, str(prov.get("rule_id", "")), str(prov.get("original_span", ""))))
        s = node.slots
        if node.kind == "relation_fact":
            entity(s["subject"], s.get("subject_text", "")); entity(s["object"], s.get("object_text", ""))
            relations.append(StructuredRelation(node.node_id, s["subject"], s["predicate"], s["object"], source_ids=(node.node_id,)))
        elif node.kind == "relation_query":
            entity(s.get("subject", ""), s.get("subject_text", "")); entity(s.get("object", ""), s.get("object_text", ""))
            relations.append(StructuredRelation(node.node_id, s.get("subject", ""), s["predicate"], s.get("object", ""), kind="query", source_ids=(node.node_id,))); intent = "relational_query"
        elif node.kind == "ordering_query":
            relations.append(StructuredRelation(node.node_id, "", "oldest", "", kind="query", source_ids=(node.node_id,))); intent = "ordering_query"
        elif node.kind == "possibility":
            relations.append(StructuredRelation(node.node_id, s["subject"], s["predicate"], s["object"], kind="possibility", source_ids=(node.node_id,)))
        elif node.kind == "boolean_fact":
            entity(s["subject"], s.get("subject_text", "")); claims.append(StructuredClaim(node.node_id, s["subject"], s["predicate"], source_ids=(node.node_id,)))
        elif node.kind == "boolean_query":
            entity(s["subject"], s.get("subject_text", "")); claims.append(StructuredClaim(node.node_id, s["subject"], s["predicate"], modality="query", source_ids=(node.node_id,))); intent = "boolean_query"
        elif node.kind == "boolean_rule": constraints.append(StructuredConstraint(node.node_id, "boolean_rule", tuple(s["antecedents"]), s["consequent"], (node.node_id,)))
        elif node.kind == "before_constraint":
            entity(s["first"], s.get("first_text", "")); entity(s["second"], s.get("second_text", "")); constraints.append(StructuredConstraint(node.node_id, "before", (s["first"], s["second"]), source_ids=(node.node_id,)))
        elif node.kind == "planning_query": intent = "planning_query"
        elif node.kind == "ambiguity": ambiguities.append(Ambiguity(s["code"], s["message"], tuple(s.get("options", [])), True, s.get("question", "")))
        elif node.kind in {"world_fact","world_query","world_event","causal_rule","action_compatibility"}: intent = "habitat_query"
        elif node.kind != "dialogue_act": warnings.append(f"non_reasoning_node:{node.node_id}:{node.kind}")

    payload = {"text": original_text, "graph": graph.to_dict(), "memory_relations": [r.relation_id for r in memory_relations], "memory_claims": [c.claim_id for c in memory_claims], "memory_constraints": [c.constraint_id for c in memory_constraints]}
    request_id = "request_" + canonical_hash(payload)[:16]
    request = ReasoningRequest(request_id, original_text, intent, tuple(claims), tuple(sorted(entities.values(), key=lambda x:x.entity_id)), tuple(relations), tuple(constraints), tuple(ambiguities), tuple(provenance), "natural_language_response", tuple(warnings), repair_actions, habitat)
    return BridgeResult("blocked" if any(x.startswith("BLOCKING:") for x in warnings) else "ok", tuple(warnings), request)
