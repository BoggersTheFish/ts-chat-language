"""Topic tracking helpers."""

from __future__ import annotations

TOPIC_ALIASES = {
    "chatbot": "TS-native chatbot language engine",
    "language compiler": "TS-native chatbot language engine",
    "language_compiler": "TS-native chatbot language engine",
    "usability": "chatbot usability parity",
    "reasoning engine": "reasoning engine (deprioritized)",
    "reasoning_engine": "reasoning engine (deprioritized)",
    "chatbot_language_layer": "TS-native chatbot language engine",
}


def normalize_topic(topic: str) -> str:
    key = topic.strip().lower()
    return TOPIC_ALIASES.get(key, topic.strip() or "general conversation")