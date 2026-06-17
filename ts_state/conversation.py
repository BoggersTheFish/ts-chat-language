"""Explicit dialogue state machine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ts_lang.graph_queries import acceptable_frame_nodes, emotion_affect, rejected_scopes
from ts_lang.meaning_graph import MeaningGraph
from ts_lang.types import CompiledTurn
from ts_state.memory import trim_history
from ts_state.topic import normalize_topic
from ts_state.turn import StateUpdateReceipt, TurnRecord


@dataclass
class ConversationState:
    current_topic: str = "general conversation"
    user_position: str | None = None
    accepted_frames: list[dict[str, Any]] = field(default_factory=list)
    rejected_frames: list[str] = field(default_factory=list)
    next_expected_action: str | None = None
    turn_history: list[TurnRecord] = field(default_factory=list)
    affect_flag: str | None = None
    turn_counter: int = 0
    last_meaning_graph: MeaningGraph | None = None
    last_graph_diff: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_topic": self.current_topic,
            "user_position": self.user_position,
            "accepted_frames": self.accepted_frames,
            "rejected_frames": self.rejected_frames,
            "next_expected_action": self.next_expected_action,
            "affect_flag": self.affect_flag,
            "turn_count": len(self.turn_history),
            "has_prior_graph": self.last_meaning_graph is not None,
        }

    def apply_compiled_turn(
        self,
        turn: CompiledTurn,
        *,
        graph_diff: dict[str, Any] | None = None,
    ) -> StateUpdateReceipt:
        self.turn_counter += 1
        updates: list[str] = []

        if turn.topic:
            new_topic = normalize_topic(turn.topic)
            if new_topic != self.current_topic:
                updates.append(f"topic:{self.current_topic}->{new_topic}")
                self.current_topic = new_topic

        act = turn.dialogue_act
        graph = turn.meaning_graph

        if act in {"correct_assistant", "reject_framing"}:
            for item in rejected_scopes(graph):
                if item not in self.rejected_frames:
                    self.rejected_frames.append(item)
                    updates.append(f"reject:{item}")
            affect = emotion_affect(graph) or turn.emotion.get("affect")
            if affect == "frustrated":
                self.affect_flag = "frustrated"
                updates.append("affect:frustrated")

        if act in {"confirm_direction", "strategic_redirect", "correct_assistant"}:
            for node in acceptable_frame_nodes(graph):
                self.accepted_frames.append(node.to_dict())
                updates.append(f"accept_graph_node:{node.kind}")
            if act == "strategic_redirect":
                self.user_position = "reasoning engine already solid; focus language layer"
                updates.append("position:language_layer_priority")
            self.next_expected_action = "design chatbot language layer"

        if act == "express_frustration":
            self.affect_flag = "frustrated"
            self.next_expected_action = "clarify user target"
            updates.append("affect:frustrated")

        if act in {"ask_for_next_step", "request_plan"}:
            self.next_expected_action = "provide implementation plan"

        if act == "ask_question":
            self.next_expected_action = "answer or clarify"

        self.last_meaning_graph = graph
        self.last_graph_diff = graph_diff or {}

        return StateUpdateReceipt(
            turn_id=self.turn_counter,
            updates=updates,
            current_topic=self.current_topic,
            rejected_frames=list(self.rejected_frames),
            accepted_frames=list(self.accepted_frames),
            graph_diff=graph_diff or {},
        )

    def record_turn(
        self,
        *,
        user_text: str,
        bot_text: str,
        compiled_turn: CompiledTurn,
        response_plan: dict[str, Any],
        graph_diff: dict[str, Any] | None = None,
    ) -> TurnRecord:
        record = TurnRecord(
            turn_id=self.turn_counter,
            user_text=user_text,
            bot_text=bot_text,
            dialogue_act=compiled_turn.dialogue_act,
            topic=self.current_topic,
            compiled_turn=compiled_turn.to_dict(),
            response_plan=response_plan,
            graph_diff=graph_diff or {},
        )
        self.turn_history.append(record)
        self.turn_history = trim_history(self.turn_history)
        return record