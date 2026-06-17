"""Core IR types for TSLC / TS-Chat v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def _to_dict(obj: Any) -> dict[str, Any]:
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    return dict(obj)


@dataclass(frozen=True)
class MarkerSet:
    negation: bool = False
    frustration: bool = False
    command: bool = False
    intensity: float = 0.0
    caps_emphasis: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NormalizedUtterance:
    raw: str
    clean: str
    tokens: list[str]
    markers: MarkerSet

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw": self.raw,
            "clean": self.clean,
            "tokens": self.tokens,
            "markers": self.markers.to_dict(),
        }


@dataclass(frozen=True)
class DialogueActResult:
    act: str
    subact: str | None = None
    meaning: dict[str, Any] = field(default_factory=dict)
    emotion: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    ambiguities: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SemanticFrame:
    schema: str
    slots: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"schema": self.schema, "slots": self.slots}


@dataclass(frozen=True)
class CompiledTurn:
    raw: str
    normalized: str
    dialogue_act: str
    subact: str | None
    semantic_frames: list[SemanticFrame]
    emotion: dict[str, Any]
    topic: str
    confidence: float
    ambiguities: list[str]
    status: str = "ok"
    repair_action: str | None = None
    known_terms: list[str] = field(default_factory=list)
    unknown_terms: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw": self.raw,
            "normalized": self.normalized,
            "dialogue_act": self.dialogue_act,
            "subact": self.subact,
            "semantic_frames": [f.to_dict() for f in self.semantic_frames],
            "emotion": self.emotion,
            "topic": self.topic,
            "confidence": self.confidence,
            "ambiguities": self.ambiguities,
            "status": self.status,
            "repair_action": self.repair_action,
            "known_terms": self.known_terms,
            "unknown_terms": self.unknown_terms,
        }


@dataclass(frozen=True)
class ResponsePlan:
    response_act: str
    main_point: str
    style: dict[str, Any]
    template_id: str
    confidence: float = 0.0
    slots: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResponseCandidate:
    candidate_id: str
    rule_id: str
    text: str
    score: float
    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RenderedReply:
    text: str
    template_id: str
    rule_id: str
    candidate_selection: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TurnReceipt:
    turn_id: int
    user_text: str
    compiled_turn: CompiledTurn
    response_plan: ResponsePlan
    rendered_reply: RenderedReply
    state_snapshot: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "user_text": self.user_text,
            "compiled_turn": self.compiled_turn.to_dict(),
            "response_plan": self.response_plan.to_dict(),
            "rendered_reply": self.rendered_reply.to_dict(),
            "state_snapshot": self.state_snapshot,
        }