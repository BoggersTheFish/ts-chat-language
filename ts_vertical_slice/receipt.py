"""Unified deterministic turn receipt."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ts_reasoner.typed_support import canonical_hash


@dataclass(frozen=True)
class TurnReceipt:
    turn_id: str
    input_text: str
    parse_status: str
    parser_rules_used: tuple[str, ...]
    parse_warnings: tuple[str, ...]
    meaning_graph_hash: str
    meaning_graph_summary: dict[str, Any]
    bridge_status: str
    bridge_warnings: tuple[str, ...]
    reasoning_request_hash: str
    verifier_decision: str
    verifier_checks: tuple[dict[str, Any], ...]
    unsupported_claims: tuple[str, ...]
    contradictions: tuple[str, ...]
    ambiguities: tuple[str, ...]
    repair_attempted: bool
    repair_actions: tuple[str, ...]
    repair_result: str | None
    final_status: str
    final_response: str
    response_template: str
    deterministic_replay_hash: str
    component_versions: dict[str, str]
    state_hash: str
    meaning_graph: dict[str, Any]
    reasoning_request: dict[str, Any]

    def to_dict(self) -> dict[str, Any]: return asdict(self)
    def write(self, root: Path) -> Path:
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{self.turn_id}_{self.deterministic_replay_hash[:10]}.json"
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path


def replay_hash(payload: dict[str, Any]) -> str: return canonical_hash(payload)
