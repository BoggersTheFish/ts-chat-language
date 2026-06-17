"""Declarative graph derivation rules from semantic frames."""

from __future__ import annotations

from typing import Any, Protocol

from ts_lang.types import SemanticFrame

_DERIVED_NODE_KINDS = frozenset(
    {"rejected_scope", "accepted_scope", "constraint", "focus_target"}
)


class GraphBuilder(Protocol):
    def add_derived_node(
        self,
        *,
        kind: str,
        value: Any,
        label: str | None = None,
        slots: dict[str, Any] | None = None,
        provenance: dict[str, Any],
        polarity: str | None = None,
    ) -> str: ...

    def add_edge(
        self,
        *,
        source_id: str,
        target_id: str,
        relation: str,
        provenance: dict[str, Any],
    ) -> None: ...


def _match_frame_rule(when: dict[str, Any], frame: SemanticFrame) -> bool:
    if "frame_schema" in when:
        return frame.schema == when["frame_schema"]
    if "frame_schema_in" in when:
        return frame.schema in when["frame_schema_in"]
    return True


def _slot_values(frame: SemanticFrame, slot: str, *, iterate: bool) -> list[Any]:
    value = frame.slots.get(slot)
    if value is None:
        return []
    if iterate:
        if isinstance(value, list):
            return list(value)
        return [value]
    if isinstance(value, list):
        return [value[0]] if value else []
    return [value]


def _resolve_slots(template: dict[str, Any], *, item: Any) -> dict[str, Any]:
    resolved: dict[str, Any] = {}
    for key, val in template.items():
        if val in {"$item", "$value"}:
            resolved[key] = item
        else:
            resolved[key] = val
    return resolved


def apply_graph_derivations(
    builder: GraphBuilder,
    *,
    frame: SemanticFrame,
    frame_node_id: str,
    frame_provenance: dict[str, Any],
    rules: list[dict[str, Any]],
) -> list[str]:
    """Apply pack graph rules; return fired rule ids."""
    fired: list[str] = []
    sorted_rules = sorted(rules, key=lambda rule: (-int(rule.get("priority", 0)), str(rule["id"])))

    for rule in sorted_rules:
        when = rule.get("when", {})
        if not _match_frame_rule(when, frame):
            continue

        derivations = rule.get("derivations", [])
        if not derivations:
            continue

        fired.append(str(rule["id"]))
        for derivation in derivations:
            slot = str(derivation.get("from_slot", ""))
            iterate = bool(derivation.get("iterate", True))
            skip_empty = bool(derivation.get("skip_empty", True))
            values = _slot_values(frame, slot, iterate=iterate)
            if skip_empty and not values:
                continue

            node_kind = str(derivation["node_kind"])
            relation = str(derivation["relation"])
            polarity = derivation.get("polarity")
            node_slots_template = derivation.get("node_slots", {"value": "$item"})
            node_prov = {**frame_provenance, **derivation.get("provenance", {})}
            edge_prov = dict(derivation.get("edge_provenance", {}))

            for item in values:
                if item is None or (isinstance(item, str) and not str(item).strip()):
                    continue
                slots = _resolve_slots(node_slots_template, item=item)
                if polarity and "polarity" not in slots:
                    slots["polarity"] = polarity

                if node_kind not in _DERIVED_NODE_KINDS:
                    continue

                target_id = builder.add_derived_node(
                    kind=node_kind,
                    value=slots.get("value", item),
                    slots=slots if slots else None,
                    provenance=node_prov,
                    polarity=str(polarity) if polarity else None,
                )
                builder.add_edge(
                    source_id=frame_node_id,
                    target_id=target_id,
                    relation=relation,
                    provenance=edge_prov,
                )

    return fired