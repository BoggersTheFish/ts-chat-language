"""Map compiled turns and state to response plans."""

from __future__ import annotations

from ts_lang.types import CompiledTurn, ResponsePlan
from ts_render.style import base_style, merge_style
from ts_state.conversation import ConversationState

ACT_TO_RESPONSE = {
    "correct_assistant": "acknowledge_and_reframe",
    "reject_framing": "acknowledge_and_reframe",
    "express_frustration": "de_escalate_and_clarify",
    "confirm_direction": "confirm_and_advance",
    "strategic_redirect": "confirm_and_advance",
    "ask_for_next_step": "provide_plan_sections",
    "request_plan": "provide_plan_sections",
    "ask_question": "answer_or_ask_clarifier",
    "ask_for_definition": "answer_or_ask_clarifier",
    "continue_topic": "continue_thread",
    "answer_simple": "confirm_and_advance",
}


def _desired_focus(turn: CompiledTurn) -> str | None:
    if turn.meaning_graph and hasattr(turn.meaning_graph, "desired_focus"):
        focus = turn.meaning_graph.desired_focus()
        if focus:
            return str(focus).replace("_", " ")
    for frame in turn.semantic_frames:
        if frame.schema in {"scope_correction", "focus_shift", "usability_target"}:
            focus = frame.slots.get("desired_focus") or frame.slots.get("new_focus")
            if focus:
                return str(focus).replace("_", " ")
    return None


def _main_point(turn: CompiledTurn, state: ConversationState) -> str:
    if turn.status == "partial_parse":
        known = ", ".join(turn.known_terms) or turn.topic
        return f"partial understanding around {known}"

    for frame in turn.semantic_frames:
        if frame.schema == "usability_target":
            return (
                "The target is usability parity, not architecture parity. "
                "The system should feel like a normal chatbot while compiling "
                "language into TS state underneath."
            )
        if frame.schema == "scope_correction":
            focus = frame.slots.get("desired_focus")
            if not focus and frame.slots.get("accepts"):
                focus = frame.slots["accepts"][0]
            rejects = frame.slots.get("rejects", [])
            if focus:
                reject_part = (
                    f", rejecting {', '.join(str(r).replace('_', ' ') for r in rejects)}"
                    if rejects
                    else ""
                )
                return f"Reframing around {str(focus).replace('_', ' ')}{reject_part}."
        if frame.schema == "focus_shift":
            new_focus = frame.slots.get("new_focus", "chatbot language layer")
            return f"Focus shifts to {new_focus.replace('_', ' ')}; reasoning engine is not the current priority."
        if frame.schema == "claim":
            return (
                f"{frame.slots.get('subject', 'The system')} "
                f"{frame.slots.get('predicate', 'has a stated claim').replace('_', ' ')}."
            )
        if frame.schema == "architecture_preference":
            prefer = frame.slots.get("prefer", [])
            if prefer:
                return f"Prefer {', '.join(p.replace('_', ' ') for p in prefer)} over exposure training."

    if turn.dialogue_act == "reject_framing":
        return "Dropping the previous framing and refocusing on the chatbot language layer."

    if turn.dialogue_act == "correct_assistant":
        focus = _desired_focus(turn) or state.current_topic
        return f"Reframing around {focus}."

    if turn.dialogue_act in {"ask_for_next_step", "request_plan"}:
        return (
            "Build the language interface now: normalizer, dialogue act compiler, "
            "semantic frames, conversation state, and renderer."
        )

    return f"Continuing on {state.current_topic}."


def _template_id(turn: CompiledTurn, response_act: str) -> str:
    if turn.status == "partial_parse":
        return "ask_targeted_question"

    for frame in turn.semantic_frames:
        if frame.schema == "usability_target":
            return "ack_correction_reframe_usability"

    mapping = {
        "acknowledge_and_reframe": "ack_correction_reframe",
        "de_escalate_and_clarify": "de_escalate_clarify",
        "confirm_and_advance": "confirm_and_advance",
        "provide_plan_sections": "provide_plan_sections",
        "answer_or_ask_clarifier": "answer_or_clarify",
        "continue_thread": "continue_thread",
        "ask_targeted_question": "ask_targeted_question",
    }
    if turn.dialogue_act == "reject_framing":
        return "reject_acknowledge"
    return mapping.get(response_act, "continue_thread")


def _plan_slots(turn: CompiledTurn, state: ConversationState, main_point: str) -> dict:
    slots = {
        "main_point": main_point,
        "topic": state.current_topic,
        "next_action": state.next_expected_action or "continue the chatbot language layer",
    }
    if turn.status == "partial_parse":
        slots["partial_meaning"] = turn.topic or "the chatbot layer"
        slots["options"] = "input parsing, response rendering, or conversation memory"
    if turn.dialogue_act in {"request_plan", "ask_for_next_step"}:
        slots["sections"] = (
            "normalizer, dialogue act compiler, semantic frame compiler, "
            "conversation state, response planner, renderer"
        )
    return slots


def plan_response(turn: CompiledTurn, state: ConversationState) -> ResponsePlan:
    if turn.status == "partial_parse":
        response_act = "ask_targeted_question"
    else:
        response_act = ACT_TO_RESPONSE.get(turn.dialogue_act, "continue_thread")

    main_point = _main_point(turn, state)
    template_id = _template_id(turn, response_act)
    style = merge_style(base_style(state.affect_flag), {"directness": "high"})

    confidence = turn.confidence
    if turn.ambiguities:
        confidence = max(0.3, confidence - 0.1 * len(turn.ambiguities))

    return ResponsePlan(
        response_act=response_act,
        main_point=main_point,
        style=style,
        template_id=template_id,
        confidence=round(confidence, 2),
        slots=_plan_slots(turn, state, main_point),
    )