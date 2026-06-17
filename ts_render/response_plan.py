"""Map compiled turns and state to response plans."""

from __future__ import annotations

from ts_state.diff_memory import build_diff_memory
from ts_lang.graph_queries import (
    has_frame_kind,
    main_point_frame_node,
    preferred_constraints,
    scope_correction_focus,
    scope_correction_rejects,
)
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
    graph = turn.meaning_graph
    if graph and hasattr(graph, "desired_focus"):
        focus = graph.desired_focus()
        if focus:
            return str(focus).replace("_", " ")
    focus = scope_correction_focus(graph)
    return focus.replace("_", " ") if focus else None


def _main_point_from_graph(turn: CompiledTurn) -> str | None:
    graph = turn.meaning_graph
    node = main_point_frame_node(graph)
    if node is None:
        return None

    if node.kind == "usability_target":
        return (
            "The target is usability parity, not architecture parity. "
            "The system should feel like a normal chatbot while compiling "
            "language into TS state underneath."
        )

    if node.kind == "scope_correction":
        focus = scope_correction_focus(graph)
        if focus:
            rejects = scope_correction_rejects(graph)
            reject_part = (
                f", rejecting {', '.join(r.replace('_', ' ') for r in rejects)}"
                if rejects
                else ""
            )
            return f"Reframing around {focus.replace('_', ' ')}{reject_part}."

    if node.kind == "focus_shift":
        new_focus = node.slots.get("new_focus", "chatbot language layer")
        return (
            f"Focus shifts to {str(new_focus).replace('_', ' ')}; "
            "reasoning engine is not the current priority."
        )

    if node.kind == "claim":
        return (
            f"{node.slots.get('subject', 'The system')} "
            f"{node.slots.get('predicate', 'has a stated claim').replace('_', ' ')}."
        )

    if node.kind == "architecture_preference":
        prefer = preferred_constraints(graph) or node.slots.get("prefer", [])
        if prefer:
            return f"Prefer {', '.join(str(p).replace('_', ' ') for p in prefer)} over exposure training."

    return None


def _apply_diff_memory(main_point: str, memory_context: str) -> str:
    if not memory_context:
        return main_point
    return f"{memory_context} {main_point}"


def _main_point(turn: CompiledTurn, state: ConversationState, memory_context: str) -> str:
    if turn.status == "partial_parse":
        known = ", ".join(turn.known_terms) or turn.topic
        return f"partial understanding around {known}"

    graph_point = _main_point_from_graph(turn)
    if graph_point:
        return _apply_diff_memory(graph_point, memory_context)

    if turn.dialogue_act == "reject_framing":
        return _apply_diff_memory(
            "Dropping the previous framing and refocusing on the chatbot language layer.",
            memory_context,
        )

    if turn.dialogue_act == "correct_assistant":
        focus = _desired_focus(turn) or state.current_topic
        return _apply_diff_memory(f"Reframing around {focus}.", memory_context)

    if turn.dialogue_act in {"ask_for_next_step", "request_plan"}:
        base = (
            "Build the language interface now: normalizer, dialogue act compiler, "
            "semantic frames, conversation state, and renderer."
        )
        return _apply_diff_memory(base, memory_context)

    return _apply_diff_memory(f"Continuing on {state.current_topic}.", memory_context)


def _template_id(
    turn: CompiledTurn,
    response_act: str,
    *,
    memory_context: str,
) -> str:
    if turn.status == "partial_parse":
        return "ask_targeted_question"

    if has_frame_kind(turn.meaning_graph, "usability_target") and not memory_context:
        return "ack_correction_reframe_usability"

    if memory_context:
        if turn.dialogue_act in {"strategic_redirect", "confirm_direction"}:
            return "confirm_shift_with_memory"
        if turn.dialogue_act in {"ask_for_next_step", "request_plan"}:
            return "provide_plan_with_memory"
        if turn.dialogue_act == "correct_assistant":
            return "ack_correction_with_memory"

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


def _plan_slots(
    turn: CompiledTurn,
    state: ConversationState,
    main_point: str,
    *,
    memory_context: str,
    diff_memory_summary: str,
) -> dict:
    slots = {
        "main_point": main_point,
        "topic": state.current_topic,
        "next_action": state.next_expected_action or "continue the chatbot language layer",
        "memory_context": memory_context,
        "diff_memory_summary": diff_memory_summary,
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

    diff_memory = build_diff_memory(state, dialogue_act=turn.dialogue_act)
    memory_context = diff_memory.memory_context

    main_point = _main_point(turn, state, memory_context)
    template_id = _template_id(turn, response_act, memory_context=memory_context)
    style = merge_style(base_style(state.affect_flag), {"directness": "high"})

    confidence = turn.confidence
    if turn.ambiguities:
        confidence = max(0.3, confidence - 0.1 * len(turn.ambiguities))
    if memory_context:
        confidence = min(1.0, round(confidence + 0.05, 2))

    return ResponsePlan(
        response_act=response_act,
        main_point=main_point,
        style=style,
        template_id=template_id,
        confidence=round(confidence, 2),
        slots=_plan_slots(
            turn,
            state,
            main_point,
            memory_context=memory_context,
            diff_memory_summary=diff_memory.summary,
        ),
    )