"""Declarative topic inference rules."""

from __future__ import annotations

from typing import Any

from ts_lang.resources import lexicon
from ts_lang.types import DialogueActResult


def _match_topic_rule(
    when: dict[str, Any],
    *,
    known_topics: list[str],
    act: DialogueActResult,
) -> bool:
    if when.get("known_topics_nonempty"):
        return bool(known_topics)
    if "act_meaning_has" in when:
        return when["act_meaning_has"] in act.meaning
    if "act_in" in when:
        return act.act in when["act_in"]
    return True


def _apply_transform(value: str, transform: str | None) -> str:
    if transform == "underscore_to_space":
        return value.replace("_", " ")
    return value


def _resolve_topic(
    resolve: dict[str, Any],
    *,
    known_topics: list[str],
    act: DialogueActResult,
    fallback: str,
) -> str | None:
    strategy = resolve.get("strategy", "fallback")

    if strategy == "topic_priority":
        priority = lexicon().get("topic_priority", [])
        for topic in priority:
            if topic in known_topics:
                return topic.replace("_", " ")
        return None

    if strategy == "act_meaning":
        key = resolve.get("key", "")
        if key not in act.meaning:
            return None
        value = str(act.meaning[key])
        return _apply_transform(value, resolve.get("transform"))

    if strategy == "fallback":
        return fallback

    return None


def infer_topic_from_rules(
    known_topics: list[str],
    act: DialogueActResult,
    fallback: str,
    rules: list[dict[str, Any]],
) -> tuple[str, list[str]]:
    """Return resolved topic and fired rule ids."""
    sorted_rules = sorted(rules, key=lambda rule: (-int(rule.get("priority", 0)), str(rule["id"])))
    fired: list[str] = []

    for rule in sorted_rules:
        when = rule.get("when", {})
        if not _match_topic_rule(when, known_topics=known_topics, act=act):
            continue
        resolve = rule.get("resolve", {})
        topic = _resolve_topic(resolve, known_topics=known_topics, act=act, fallback=fallback)
        if topic is not None:
            fired.append(str(rule["id"]))
            return topic, fired

    return fallback, fired