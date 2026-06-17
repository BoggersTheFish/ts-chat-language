"""Short rolling conversation memory."""

from __future__ import annotations

from ts_state.turn import TurnRecord

DEFAULT_MEMORY_LIMIT = 8


def trim_history(history: list[TurnRecord], limit: int = DEFAULT_MEMORY_LIMIT) -> list[TurnRecord]:
    if len(history) <= limit:
        return history
    return history[-limit:]