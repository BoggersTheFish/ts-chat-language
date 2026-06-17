"""Explicit dialogue state machine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

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

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_topic": self.current_topic,
            "user_position": self.user_position,
            "accepted_frames": self.accepted_frames,
            "rejected_frames": self.rejected_frames,
            "next_expected_action": self.next_expected_action,
            "affect_flag": self.affect_flag,
            "turn_count": len(self.turn_history),
        }

    def apply_compiled_turn(self, turn: CompiledTurn) -> StateUpdateReceipt:
        self.turn_counter += 1
        updates: list[str] = []

        if turn.topic:
            new_topic = normalize_topic(turn.topic)
            if new_topic != self.current_topic:
                updates.append(f"topic:{self.current_topic}->{new_topic}")
                self.current_topic = new_topic

        act = turn.dialogue_act

        if act in {"correct_assistant", "reject_framing"}:
            for frame in turn.semantic_frames:
                if frame.schema == "scope_correction":
                    for item in frame.slots.get("rejects", []):
                        if item not in self.rejected_frames:
                            self.rejected_frames.append(str(item))
                            updates.append(f"reject:{item}")
            if turn.emotion.get("affect") == "frustrated":
                self.affect_flag = "frustrated"
                updates.append("affect:frustrated")

        if act in {"confirm_direction", "strategic_redirect", "correct_assistant"}:
            for frame in turn.semantic_frames:
                if frame.schema in {"scope_correction", "focus_shift", "usability_target", "claim"}:
                    self.accepted_frames.append(frame.to_dict())
                    updates.append(f"accept_frame:{frame.schema}")
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

        return StateUpdateReceipt(
            turn_id=self.turn_counter,
            updates=updates,
            current_topic=self.current_topic,
            rejected_frames=list(self.rejected_frames),
            accepted_frames=list(self.accepted_frames),
        )

    def record_turn(
        self,
        *,
        user_text: str,
        bot_text: str,
        compiled_turn: CompiledTurn,
        response_plan: dict[str, Any],
    ) -> TurnRecord:
        record = TurnRecord(
            turn_id=self.turn_counter,
            user_text=user_text,
            bot_text=bot_text,
            dialogue_act=compiled_turn.dialogue_act,
            topic=self.current_topic,
            compiled_turn=compiled_turn.to_dict(),
            response_plan=response_plan,
        )
        self.turn_history.append(record)
        self.turn_history = trim_history(self.turn_history)
        return record