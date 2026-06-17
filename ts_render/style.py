"""Style profiles for rendered replies."""

from __future__ import annotations

from typing import Any


def base_style(affect_flag: str | None = None) -> dict[str, Any]:
    style = {"directness": "medium", "warmth": "medium", "technical_density": "medium"}
    if affect_flag == "frustrated":
        style["directness"] = "high"
        style["warmth"] = "low"
    return style


def merge_style(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    merged.update(override)
    return merged