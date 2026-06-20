"""Verifier-gated deterministic natural-language renderer."""

from __future__ import annotations

from dataclasses import dataclass

from ts_reasoner.structured_request import ReasoningRequest, VerifierDecision


@dataclass(frozen=True)
class RenderResult:
    text: str
    template_id: str
    support_validated: bool


def _title(value: str) -> str:
    return value.replace("_", " ").strip().capitalize()


def render_verified(decision: VerifierDecision, request: ReasoningRequest) -> RenderResult:
    answer = decision.answer
    known_support = {r.relation_id for r in request.relations} | {c.claim_id for c in request.claims} | {c.constraint_id for c in request.constraints}
    affirmative = decision.decision == "ACCEPT" or decision.repair_result == "REPAIR_ACCEPTED"
    if affirmative:
        if not answer.support_ids or not set(answer.support_ids) <= known_support:
            raise AssertionError("renderer attempted an affirmative claim without verifier-approved support")

    entities = {entity.entity_id: entity.name for entity in request.entities}
    name = lambda value: entities.get(value, value.replace("_", " "))
    if answer.answer_type == "recorded": return RenderResult("Recorded as a user-provided premise.", "ACCEPT_RECORDED", True)
    if answer.answer_type == "ordering": return RenderResult(f"{_title(name(answer.subject))} is the {answer.property}.", "ACCEPT_ORDERING", True)
    if answer.answer_type == "fact":
        if answer.predicate == "opens": text = f"The {name(answer.subject)} opens the {name(answer.object)}."
        else: text = f"{_title(name(answer.subject))} {answer.predicate.replace('_',' ')} {name(answer.object)}."
        return RenderResult(text, "ACCEPT_FACT", True)
    if answer.answer_type == "boolean": return RenderResult(f"The {name(answer.subject)} is {answer.predicate.removeprefix(answer.subject + '_').replace('_',' ')}.", "ACCEPT_BOOLEAN", True)
    if answer.answer_type == "plan": return RenderResult(f"{_title(name(answer.subject))} before {name(answer.object)}.", "ACCEPT_PLAN", True)
    if answer.answer_type == "clarification": return RenderResult(f"I found more than one possible interpretation. {answer.clarification}", "REPAIR_CLARIFICATION", True)
    if decision.reason == "contradiction": return RenderResult(f"I cannot provide a supported answer because the available statements conflict: {decision.contradictions[0]}", "REJECT_CONTRADICTION", True)

    query = next((r for r in request.relations if r.kind == "query"), None)
    if query:
        if query.predicate == "is_a": claim = f"{_title(name(query.subject_id))} is {name(query.object_id)}"
        elif query.object_id: claim = f"{_title(name(query.subject_id))} {query.predicate.replace('_',' ')} {name(query.object_id)}"
        else: claim = "the requested conclusion"
    else:
        claim = answer.claim.replace("_", " ") or "the requested conclusion"
    return RenderResult(f"There is not enough supported information to conclude that {claim}.", "REJECT_INSUFFICIENT_SUPPORT", True)
