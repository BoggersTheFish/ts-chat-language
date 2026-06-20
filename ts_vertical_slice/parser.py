"""Bounded deterministic language parser producing the canonical MeaningGraph."""

from __future__ import annotations

import re
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from ts_lang.meaning_graph import MeaningEdge, MeaningGraph, MeaningNode, semantic_slug


@dataclass(frozen=True)
class ParseResult:
    graph: MeaningGraph
    status: str
    rules_used: tuple[str, ...]
    warnings: tuple[str, ...]
    repair_actions: tuple[str, ...] = ()


def _entity(text: str) -> str:
    text = re.sub(r"^(?:the|a|an)\s+", "", text.strip(), flags=re.I)
    return semantic_slug(text)


def _display(text: str) -> str:
    return re.sub(r"^(?:the|a|an)\s+", "", text.strip(), flags=re.I)


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text.strip()) if part.strip()]


def parse_to_meaning_graph(text: str) -> ParseResult:
    nodes: list[MeaningNode] = []
    edges: list[MeaningEdge] = []
    rules: list[str] = []
    warnings: list[str] = []
    repairs: list[str] = []
    root = MeaningNode("node_act_root", "dialogue_act", "reasoning_input", {"raw": text}, {"source_type": "user_input", "source_id": "turn"})
    nodes.append(root)

    def add(kind: str, slots: dict[str, Any], rule: str, span: str) -> None:
        key = f"{kind}:{rule}:{slots}"
        node_id = f"node_{kind}_{sha256(key.encode()).hexdigest()[:12]}"
        prov = {"source_type": "deterministic_rule", "source_id": node_id, "rule_id": rule, "original_span": span}
        node = MeaningNode(node_id, kind, kind.replace("_", " "), slots, prov)
        nodes.append(node)
        edges.append(MeaningEdge(f"edge_{node_id}_expresses", root.node_id, node_id, "expresses", prov))
        rules.append(rule)

    consumed = 0
    for sentence in _sentences(text):
        plain = sentence.rstrip(".?!").strip()
        match = re.fullmatch(r"(.+?)\s+is\s+older\s+than\s+(.+)", plain, re.I)
        if match:
            add("relation_fact", {"subject": _entity(match[1]), "subject_text": _display(match[1]), "predicate": "older_than", "object": _entity(match[2]), "object_text": _display(match[2])}, "relation.older_than", sentence); consumed += 1; continue
        match = re.fullmatch(r"(.+?)\s+opens\s+(.+)", plain, re.I)
        if match:
            add("relation_fact", {"subject": _entity(match[1]), "subject_text": _display(match[1]), "predicate": "opens", "object": _entity(match[2]), "object_text": _display(match[2])}, "relation.opens", sentence); consumed += 1; continue
        match = re.fullmatch(r"which\s+door\s+does\s+(.+?)\s+open", plain, re.I)
        if match:
            add("relation_query", {"subject": _entity(match[1]), "subject_text": _display(match[1]), "predicate": "opens", "object": ""}, "query.opens", sentence); consumed += 1; continue
        if re.fullmatch(r"who\s+is\s+(?:the\s+)?oldest(?:\s+one)?", plain, re.I):
            if "one" in plain.lower(): repairs.append("normalise_alias:oldest_one->oldest")
            add("ordering_query", {"predicate": "oldest"}, "query.oldest", sentence); consumed += 1; continue

        match = re.fullmatch(r"the\s+(.+?)\s+activates\s+if\s+the\s+(.+?)\s+is\s+(.+?)\s+and\s+the\s+(.+?)\s+is\s+(.+)", plain, re.I)
        if match:
            consequent = f"{_entity(match[1])}_active"
            antecedents = (f"{_entity(match[2])}_{_entity(match[3])}", f"{_entity(match[4])}_{_entity(match[5])}")
            add("boolean_rule", {"antecedents": list(antecedents), "consequent": consequent}, "boolean.conjunction", sentence); consumed += 1; continue
        match = re.fullmatch(r"the\s+(.+?)\s+is\s+(.+)", plain, re.I)
        if match:
            predicate = f"{_entity(match[1])}_{_entity(match[2])}"
            add("boolean_fact", {"subject": _entity(match[1]), "subject_text": _display(match[1]), "predicate": predicate}, "boolean.fact", sentence); consumed += 1; continue
        match = re.fullmatch(r"is\s+the\s+(.+?)\s+(.+)", plain, re.I)
        if match:
            predicate = f"{_entity(match[1])}_{_entity(match[2])}"
            add("boolean_query", {"subject": _entity(match[1]), "subject_text": _display(match[1]), "predicate": predicate}, "boolean.query", sentence); consumed += 1; continue

        match = re.fullmatch(r"([A-Z][\w-]*)\s+is\s+(?:an?\s+)?(.+)", plain)
        if match:
            add("relation_fact", {"subject": _entity(match[1]), "subject_text": match[1], "predicate": "is_a", "object": _entity(match[2]), "object_text": _display(match[2])}, "classification.fact", sentence); consumed += 1; continue
        match = re.fullmatch(r"(.+?)s?\s+(?:can\s+become|sometimes)\s+(.+)", plain, re.I)
        if match:
            add("possibility", {"subject": _entity(match[1]), "subject_text": _display(match[1]), "predicate": _entity(match[2]), "object": _entity(match[2])}, "possibility.non_entailing", sentence); consumed += 1; continue
        match = re.fullmatch(r"(?:is|does)\s+([A-Z][\w-]*)\s+(.+)", plain, re.I)
        if match:
            add("relation_query", {"subject": _entity(match[1]), "subject_text": match[1], "predicate": "is_a", "object": _entity(match[2]), "object_text": _display(match[2])}, "classification.query", sentence); consumed += 1; continue

        match = re.fullmatch(r"([A-Z][\w-]*)\s+gave\s+([A-Z][\w-]*)\s+her\s+(.+)", plain)
        if match:
            add("ambiguity", {"code": "ambiguous_possessive", "message": f"'her' could refer to {match[1]} or {match[2]}", "options": [_entity(match[1]), _entity(match[2])], "question": f"Did {match[1]} or {match[2]} own the {_display(match[3])}?"}, "ambiguity.pronoun", sentence); consumed += 1; continue
        if re.fullmatch(r"who\s+owns\s+the\s+.+", plain, re.I):
            add("relation_query", {"subject": "", "predicate": "owns", "object": _entity(re.sub(r"who\s+owns\s+", "", plain, flags=re.I))}, "query.owns", sentence); consumed += 1; continue

        match = re.fullmatch(r"i\s+(?:must|need\s+to)\s+(.+?)\s+before\s+(.+)", plain, re.I)
        if match:
            add("before_constraint", {"first": _entity(match[1]), "first_text": _display(match[1]), "second": _entity(match[2]), "second_text": _display(match[2])}, "planning.before", sentence); consumed += 1; continue
        if re.fullmatch(r"what\s+(?:should|must)\s+happen\s+(?:first|1st)", plain, re.I):
            if "1st" in plain.lower(): repairs.append("normalise_alias:1st->first")
            add("planning_query", {"requested": "first"}, "planning.query", sentence); consumed += 1; continue

        warnings.append(f"unsupported_sentence:{sentence}")

    if consumed == 0:
        add("ambiguity", {"code": "unsupported_grammar", "message": "The input is outside the bounded grammar.", "options": [], "question": "Could you restate this as a supported relation, Boolean rule, or before/after constraint?"}, "parser.unsupported", text)
    graph = MeaningGraph(nodes, edges, root.node_id, f"{len(nodes)-1} bounded reasoning structures")
    return ParseResult(graph, "ok" if consumed else "partial_parse", tuple(rules), tuple(warnings), tuple(repairs))
