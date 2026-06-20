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


@dataclass
class VerifiedState:
    relations: list[StructuredRelation] = field(default_factory=list)
    claims: list[StructuredClaim] = field(default_factory=list)
    constraints: list[StructuredConstraint] = field(default_factory=list)

    def to_dict(self):
        return {"relations":[r.__dict__ for r in self.relations],"claims":[c.__dict__ for c in self.claims],"constraints":[c.__dict__ for c in self.constraints]}
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
        bridge = bridge_meaning_graph(parsed.graph, text, memory_relations=self.state.relations, memory_claims=self.state.claims, memory_constraints=self.state.constraints, repair_actions=parsed.repair_actions)
        decision = verify_reasoning_request(bridge.request)
        rendered = render_verified(decision, bridge.request)
        if decision.decision == "ACCEPT" or decision.repair_result == "REPAIR_ACCEPTED": self._commit_current(bridge.request, parsed.graph)
        state_hash = self.state.hash
        stable = {"input":text,"graph_hash":graph_hash,"request_hash":bridge.request.canonical_hash,"decision":decision.to_dict(),"response":rendered.text,"template":rendered.template_id,"state_hash":state_hash}
        receipt = TurnReceipt(
            f"turn_{self.turn_count:04d}", text, parsed.status, parsed.rules_used, parsed.warnings,
            graph_hash, {"summary":parsed.graph.summary,"node_count":len(parsed.graph.nodes),"edge_count":len(parsed.graph.edges)},
            bridge.status, bridge.warnings, bridge.request.canonical_hash, decision.decision,
            tuple(check.__dict__ for check in decision.checks), decision.unsupported_claims, decision.contradictions,
            decision.ambiguities, decision.repair_attempted, decision.repair_actions, decision.repair_result,
            decision.decision, rendered.text, rendered.template_id, replay_hash(stable),
            {"ts-chat-language":"0.8.0","ts-vertical-slice":__version__,"ts-reasoner-v0":"40.0.0"}, state_hash, graph_dict, bridge.request.to_dict(),
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
