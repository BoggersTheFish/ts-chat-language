"""Turn records and state update receipts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class TurnRecord:
    turn_id: int
    user_text: str
    bot_text: str
    dialogue_act: str
    topic: str
    compiled_turn: dict[str, Any] = field(default_factory=dict)
    response_plan: dict[str, Any] = field(default_factory=dict)
    graph_diff: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StateUpdateReceipt:
    turn_id: int
    updates: list[str]
    current_topic: str
    rejected_frames: list[str]
    accepted_frames: list[dict[str, Any]]
    graph_diff: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)