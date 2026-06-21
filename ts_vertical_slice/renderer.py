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
    if request.habitat:
        known_support |= {str(item["semantic_id"]) for item in request.habitat.get("facts",())}
        known_support |= {str(item["semantic_id"]) for item in request.habitat.get("rules",())}
        known_support |= {str(item["derived_id"]) for item in decision.causal_derivations}
        known_support |= {sid for step in decision.planning.get("chosen_plan",()) for sid in step.get("support_ids",())}
    affirmative = decision.decision == "ACCEPT" or decision.repair_result == "REPAIR_ACCEPTED"
    if affirmative:
        if not answer.support_ids or not set(answer.support_ids) <= known_support:
            raise AssertionError("renderer attempted an affirmative claim without verifier-approved support")

    entities = {entity.entity_id: entity.name for entity in request.entities}
    name = lambda value: entities.get(value, value.replace("_", " "))
    if answer.answer_type == "recorded": return RenderResult("Recorded as a user-provided premise.", "ACCEPT_RECORDED", True)
    if answer.answer_type == "signed_false": return RenderResult(f"The {name(answer.subject)} is not {answer.predicate.replace('_',' ')}.", "ACCEPT_SIGNED_FALSE", True)
    if answer.answer_type in {"state","boolean_query"}:
        text=f"The {name(answer.subject)} is {answer.predicate.replace('_',' ')}."
        if len(decision.causal_derivations)>1: text += " This is derived through the verified causal chain."
        return RenderResult(text,"ACCEPT_DERIVED_STATE" if decision.causal_derivations else "ACCEPT_SIGNED_STATE",True)
    if answer.answer_type == "owner": return RenderResult(f"{_title(name(answer.subject))} owns the {name(answer.object)}.","ACCEPT_OWNER",True)
    if answer.answer_type == "location":
        direct,_,outer=answer.object.partition("@")
        text=f"The {name(answer.subject)} is {answer.predicate} the {name(direct)}"
        if outer:text+=f", and the {name(direct)} is in the {name(outer)}"
        return RenderResult(text+".","ACCEPT_LOCATION_CHAIN",True)
    if answer.answer_type == "plan" and answer.plan_steps:
        lines=[f"{step['step_index']}. {step['action']}." for step in answer.plan_steps]
        return RenderResult("\n".join(lines),"ACCEPT_VERIFIED_PLAN",True)
    if answer.answer_type == "ordering": return RenderResult(f"{_title(name(answer.subject))} is the {answer.property}.", "ACCEPT_ORDERING", True)
    if answer.answer_type == "fact":
        if answer.predicate == "opens": text = f"The {name(answer.subject)} opens the {name(answer.object)}."
        else: text = f"{_title(name(answer.subject))} {answer.predicate.replace('_',' ')} {name(answer.object)}."
        return RenderResult(text, "ACCEPT_FACT", True)
    if answer.answer_type == "boolean": return RenderResult(f"The {name(answer.subject)} is {answer.predicate.removeprefix(answer.subject + '_').replace('_',' ')}.", "ACCEPT_BOOLEAN", True)
    if answer.answer_type == "plan": return RenderResult(f"{_title(name(answer.subject))} before {name(answer.object)}.", "ACCEPT_PLAN", True)
    if answer.answer_type == "clarification": return RenderResult(f"I found more than one possible interpretation. {answer.clarification}", "REPAIR_CLARIFICATION", True)
    if decision.reason in {"contradiction","conflicted"}: return RenderResult(f"I cannot provide a supported answer because the available statements conflict: {decision.contradictions[0]}", "REJECT_CONTRADICTION", True)
    if decision.reason == "unreachable": return RenderResult("I cannot construct a supported plan within the bounded habitat because required preconditions are missing.","REJECT_UNREACHABLE",True)

    query = next((r for r in request.relations if r.kind == "query"), None)
    if query:
        if query.predicate == "is_a": claim = f"{_title(name(query.subject_id))} is {name(query.object_id)}"
        elif query.object_id: claim = f"{_title(name(query.subject_id))} {query.predicate.replace('_',' ')} {name(query.object_id)}"
        else: claim = "the requested conclusion"
    else:
        claim = answer.claim.replace("_", " ") or "the requested conclusion"
    return RenderResult(f"There is not enough supported information to conclude that {claim}.", "REJECT_INSUFFICIENT_SUPPORT", True)
