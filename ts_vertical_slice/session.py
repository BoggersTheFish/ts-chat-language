"""End-to-end verifier-first session with gated memory."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ts_reasoner.structured_request import StructuredClaim, StructuredConstraint, StructuredRelation, verify_reasoning_request
from ts_reasoner.typed_support import canonical_hash

from . import __version__
from .bridge import bridge_meaning_graph
from .parser import parse_to_meaning_graph
from .receipt import TurnReceipt, replay_hash
from .renderer import render_verified
from .habitat import SemanticMemory


@dataclass
class VerifiedState:
    relations: list[StructuredRelation] = field(default_factory=list)
    claims: list[StructuredClaim] = field(default_factory=list)
    constraints: list[StructuredConstraint] = field(default_factory=list)
    world: SemanticMemory = field(default_factory=SemanticMemory)

    def to_dict(self):
        return {"relations":[r.__dict__ for r in self.relations],"claims":[c.__dict__ for c in self.claims],"constraints":[c.__dict__ for c in self.constraints],"world":self.world.to_dict()}
    @property
    def hash(self): return canonical_hash(self.to_dict())


class VerticalSliceSession:
    def __init__(self, artifact_dir: str | Path = "artifacts/turns") -> None:
        self.state = VerifiedState(); self.turn_count = 0; self.artifact_dir = Path(artifact_dir); self.last_receipt=None; self.last_path=None

    def reset(self) -> str:
        self.state = VerifiedState(); self.turn_count = 0; self.last_receipt=None; self.last_path=None
        return self.state.hash

    def handle(self, text: str, *, save: bool = True) -> TurnReceipt:
        self.turn_count += 1
        parsed = parse_to_meaning_graph(text)
        graph_dict = parsed.graph.to_dict(); graph_hash = canonical_hash(graph_dict)
        is_habitat=any(node.kind in {"world_fact","world_query","world_event","causal_rule","action_compatibility"} for node in parsed.graph.nodes)
        staged=self.state.world.stage(parsed.graph,self.turn_count)
        merge_preview=self.state.world.merge_preview(staged)
        activation=self.state.world.activate(staged)
        habitat_payload=None
        if is_habitat:
            habitat_payload=self.state.world.payload(staged,activation)
        bridge = bridge_meaning_graph(parsed.graph, text, memory_relations=() if is_habitat else self.state.relations, memory_claims=() if is_habitat else self.state.claims, memory_constraints=() if is_habitat else self.state.constraints, repair_actions=parsed.repair_actions, habitat=habitat_payload)
        decision = verify_reasoning_request(bridge.request)
        rendered = render_verified(decision, bridge.request)
        memory_update={"committed":False,"before_state_hash":self.state.world.hash,"after_state_hash":self.state.world.hash,"added_semantic_ids":[],"merged_semantic_ids":[],"superseded_semantic_ids":[]}
        if decision.decision == "ACCEPT" or decision.repair_result == "REPAIR_ACCEPTED":
            if is_habitat: memory_update=self.state.world.commit(staged,decision.approved_memory_ids)
            else:
                memory_update=self.state.world.commit(staged,(item.semantic_id for item in staged.items))
                self._commit_current(bridge.request, parsed.graph)
        state_hash = self.state.hash
        transition_receipts=()
        if staged.events and memory_update.get("committed"):
            event_checks=tuple(check for check in (item.__dict__ for item in decision.checks) if check["check_id"]=="event_precondition_supported")
            transition_receipts=tuple({
                "prior_state_hash":memory_update.get("before_state_hash"),"triggering_event":event,
                "checked_preconditions":event_checks,"applied_effects":event.get("effects",()),
                "resulting_state_hash":memory_update.get("after_state_hash"),
                "superseded_evidence":tuple(memory_update.get("superseded_semantic_ids",())),
                "provenance_ids":tuple(event.get("source_ids",())),
            } for event in staged.events)
        stable = {"input":text,"graph_hash":graph_hash,"request_hash":bridge.request.canonical_hash,"decision":decision.to_dict(),"response":rendered.text,"template":rendered.template_id,"state_hash":state_hash}
        receipt = TurnReceipt(
            f"turn_{self.turn_count:04d}", text, parsed.status, parsed.rules_used, parsed.warnings,
            graph_hash, {"summary":parsed.graph.summary,"node_count":len(parsed.graph.nodes),"edge_count":len(parsed.graph.edges)},
            bridge.status, bridge.warnings, bridge.request.canonical_hash, decision.decision,
            tuple(check.__dict__ for check in decision.checks), decision.unsupported_claims, decision.contradictions,
            decision.ambiguities, decision.repair_attempted, decision.repair_actions, decision.repair_result,
            decision.decision, rendered.text, rendered.template_id, replay_hash(stable),
            {"ts-chat-language":"0.8.0","ts-vertical-slice":__version__,"ts-reasoner-v0":"40.0.0"}, state_hash, graph_dict, bridge.request.to_dict(),
            "ts-turn-receipt-v2",merge_preview,activation.to_dict() if activation else {},decision.signed_world_state,
            tuple(staged.events),transition_receipts,
            decision.causal_derivations,decision.planning,decision.decision_subtype,memory_update,
            {"input_state_hash":memory_update.get("before_state_hash"),"output_state_hash":state_hash,"deterministic_replay_hash":replay_hash(stable)},
        )
        self.last_receipt=receipt
        if save: self.last_path=receipt.write(self.artifact_dir)
        return receipt

    def _commit_current(self, request, graph) -> None:
        current={node.node_id for node in graph.nodes}
        existing={r.relation_id for r in self.state.relations}
        self.state.relations.extend(r for r in request.relations if r.kind=="fact" and r.relation_id in current and r.relation_id not in existing)
        existing={c.claim_id for c in self.state.claims}
        self.state.claims.extend(c for c in request.claims if c.modality=="asserted" and c.claim_id in current and c.claim_id not in existing)
        existing={c.constraint_id for c in self.state.constraints}
        self.state.constraints.extend(c for c in request.constraints if c.constraint_id in current and c.constraint_id not in existing)
