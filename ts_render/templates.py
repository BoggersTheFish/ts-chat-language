"""Template registry and slot filling."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from ts_lang.resources import render_templates


@lru_cache(maxsize=1)
def _templates_by_id() -> dict[str, dict]:
    return {entry["template_id"]: entry for entry in render_templates()}


@lru_cache(maxsize=1)
def _templates_by_act() -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for entry in render_templates():
        grouped.setdefault(entry["response_act"], []).append(entry)
    return grouped


def get_template(template_id: str) -> dict | None:
    return _templates_by_id().get(template_id)


def templates_for_act(response_act: str) -> list[dict]:
    return list(_templates_by_act().get(response_act, []))


def fill_template(text: str, slots: dict[str, Any]) -> str:
    rendered = text
    for key, value in slots.items():
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        rendered = rendered.replace("{" + key + "}", str(value))
    return rendered