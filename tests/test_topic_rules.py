import unittest

from ts_lang.resources import reload_resources, topic_rules
from ts_lang.topic_rules import infer_topic_from_rules
from ts_lang.types import DialogueActResult
from ts_packs.loader import reset_registry_cache


class TopicRulesTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_registry_cache()
        reload_resources()

    def test_topic_priority_rule(self) -> None:
        act = DialogueActResult(act="correct_assistant", meaning={}, confidence=0.9)
        topic, fired = infer_topic_from_rules(
            ["chatbot", "architecture"],
            act,
            "conversation",
            topic_rules(),
        )
        self.assertEqual(topic, "chatbot")
        self.assertIn("topic_priority", fired)

    def test_new_focus_rule_with_transform(self) -> None:
        act = DialogueActResult(
            act="strategic_redirect",
            meaning={"new_focus": "reasoning_engine"},
            confidence=0.9,
        )
        topic, fired = infer_topic_from_rules([], act, "conversation", topic_rules())
        self.assertEqual(topic, "reasoning engine")
        self.assertIn("meaning_new_focus", fired)

    def test_desired_focus_rule(self) -> None:
        act = DialogueActResult(
            act="correct_assistant",
            meaning={"desired_focus": "chatbot_usability"},
            confidence=0.9,
        )
        topic, fired = infer_topic_from_rules([], act, "conversation", topic_rules())
        self.assertEqual(topic, "chatbot_usability")
        self.assertIn("meaning_desired_focus", fired)

    def test_fallback_rule(self) -> None:
        act = DialogueActResult(act="ask_next", meaning={}, confidence=0.9)
        topic, fired = infer_topic_from_rules([], act, "conversation", topic_rules())
        self.assertEqual(topic, "conversation")
        self.assertIn("fallback", fired)


if __name__ == "__main__":
    unittest.main()