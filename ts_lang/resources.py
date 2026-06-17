"""Load compiled language resources from active packs."""

from __future__ import annotations

from typing import Any

from ts_packs.loader import active_registry, reset_registry_cache


def _registry():
    return active_registry()


def active_packs() -> list[str]:
    return list(_registry().active_packs)


def pack_info() -> dict[str, Any]:
    return _registry().to_dict()


def dialogue_acts() -> list[dict]:
    return list(_registry().dialogue_acts)


def phrase_patterns() -> list[dict]:
    return list(_registry().phrase_patterns)


def semantic_rules() -> list[dict]:
    return list(_registry().semantic_rules)


def frame_schemas() -> dict:
    return dict(_registry().frame_schemas)


def render_templates() -> list[dict]:
    return list(_registry().templates)


def lexicon() -> dict:
    return dict(_registry().lexicon)


def reload_resources() -> None:
    reset_registry_cache()