"""Surface renderer with inspectable candidate selection."""

from __future__ import annotations

from ts_lang.types import RenderedReply, ResponseCandidate, ResponsePlan
from ts_render.templates import fill_template, get_template, templates_for_act
from ts_state.conversation import ConversationState


def _score_candidate(
    candidate: ResponseCandidate,
    plan: ResponsePlan,
    state: ConversationState,
) -> ResponseCandidate:
    score = candidate.score
    reasons = list(candidate.reasons)

    if candidate.rule_id == plan.template_id:
        score += 0.25
        reasons.append("template_id_match")
    if plan.response_act in candidate.rule_id or plan.template_id.startswith(plan.response_act.split("_")[0]):
        score += 0.1
        reasons.append("response_act_alignment")
    if state.current_topic.lower() in candidate.text.lower():
        score += 0.05
        reasons.append("topic_continuity")
    if state.affect_flag == "frustrated" and "Got it" in candidate.text:
        score += 0.1
        reasons.append("frustration_style_fit")

    return ResponseCandidate(
        candidate_id=candidate.candidate_id,
        rule_id=candidate.rule_id,
        text=candidate.text,
        score=round(score, 3),
        reasons=reasons,
    )


def generate_candidates(plan: ResponsePlan, state: ConversationState) -> list[ResponseCandidate]:
    candidates: list[ResponseCandidate] = []

    primary = get_template(plan.template_id)
    if primary:
        text = fill_template(primary["text"], plan.slots)
        candidates.append(
            ResponseCandidate(
                candidate_id="cand_0001",
                rule_id=plan.template_id,
                text=text,
                score=0.8,
                reasons=["primary_template"],
            )
        )

    for entry in templates_for_act(plan.response_act):
        if entry["template_id"] == plan.template_id:
            continue
        text = fill_template(entry["text"], plan.slots)
        candidates.append(
            ResponseCandidate(
                candidate_id=f"cand_{len(candidates) + 1:04d}",
                rule_id=entry["template_id"],
                text=text,
                score=0.55,
                reasons=["alternate_template"],
            )
        )

    if not candidates:
        fallback = plan.main_point or f"Continuing on {state.current_topic}."
        candidates.append(
            ResponseCandidate(
                candidate_id="cand_fallback",
                rule_id="fallback",
                text=fallback,
                score=0.4,
                reasons=["no_template_match"],
            )
        )

    return [_score_candidate(c, plan, state) for c in candidates]


def select_candidate(candidates: list[ResponseCandidate]) -> tuple[ResponseCandidate, dict]:
    ranked = sorted(candidates, key=lambda c: c.score, reverse=True)
    winner = ranked[0]
    selection = {
        "selected_candidate_id": winner.candidate_id,
        "rule_id": winner.rule_id,
        "score": winner.score,
        "reasons": winner.reasons,
        "candidate_count": len(candidates),
        "alternatives": [
            {"candidate_id": c.candidate_id, "rule_id": c.rule_id, "score": c.score}
            for c in ranked[1:3]
        ],
    }
    return winner, selection


def render_response(plan: ResponsePlan, state: ConversationState) -> RenderedReply:
    candidates = generate_candidates(plan, state)
    winner, selection = select_candidate(candidates)
    return RenderedReply(
        text=winner.text,
        template_id=plan.template_id,
        rule_id=winner.rule_id,
        candidate_selection=selection,
    )