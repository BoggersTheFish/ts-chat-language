import os
import unittest

from ts_packs.loader import load_packs, reset_registry_cache
from ts_lang.resources import (
    active_packs,
    dialogue_acts,
    graph_rules,
    phrase_patterns,
    reload_resources,
    semantic_rules,
    topic_rules,
)


class PackLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_registry_cache()
        reload_resources()

    def tearDown(self) -> None:
        os.environ.pop("TSLC_PACKS", None)
        reset_registry_cache()
        reload_resources()

    def test_default_packs_load_and_merge(self) -> None:
        registry = load_packs(("base_dialogue", "ts_architecture"))
        self.assertEqual(registry.active_packs, ["base_dialogue", "ts_architecture"])
        self.assertGreater(len(registry.dialogue_acts), 0)
        self.assertGreater(len(registry.phrase_patterns), 0)
        self.assertGreater(len(registry.semantic_rules), 0)
        self.assertGreater(len(registry.graph_rules), 0)
        self.assertGreater(len(registry.topic_rules), 0)
        self.assertGreater(len(registry.templates), 0)
        self.assertIn("chatbot", registry.lexicon.get("topics", {}))

    def test_ts_architecture_phrases_merged(self) -> None:
        phrases = phrase_patterns()
        ids = {entry["phrase"] for entry in phrases}
        self.assertIn("same usability", ids)
        self.assertIn("nah bro", ids)

    def test_later_pack_overrides_template_id(self) -> None:
        registry = load_packs(("base_dialogue", "ts_architecture"))
        template_ids = {entry["template_id"] for entry in registry.templates}
        self.assertIn("ack_correction_reframe_usability", template_ids)
        self.assertIn("confirm_shift_with_memory", template_ids)

    def test_env_override_active_packs(self) -> None:
        os.environ["TSLC_PACKS"] = "base_dialogue"
        reset_registry_cache()
        reload_resources()
        self.assertEqual(active_packs(), ["base_dialogue"])
        rules = semantic_rules()
        rule_ids = {rule["id"] for rule in rules}
        self.assertIn("emotion_frame", rule_ids)
        self.assertNotIn("usability_target", rule_ids)

    def test_invalid_regex_raises(self) -> None:
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            pack_dir = Path(tmp) / "bad_pack"
            pack_dir.mkdir()
            (pack_dir / "pack.json").write_text(
                '{"id":"bad_pack","version":"0.1.0","priority":1}',
                encoding="utf-8",
            )
            (pack_dir / "semantic_rules.json").write_text(
                '{"rules":[{"id":"bad","when":{"text_regex":"[unclosed"},"emit":{"schema":"claim","slots":{}}}]}',
                encoding="utf-8",
            )
            from ts_packs import loader as pack_loader

            original = pack_loader.PACKS_DIR
            pack_loader.PACKS_DIR = Path(tmp)
            try:
                with self.assertRaises(ValueError):
                    load_packs(("bad_pack",))
            finally:
                pack_loader.PACKS_DIR = original

    def test_active_registry_matches_dialogue_act_count(self) -> None:
        acts = dialogue_acts()
        self.assertEqual(len(acts), 11)

    def test_graph_and_topic_rules_loaded_from_base_pack(self) -> None:
        graph_rule_ids = {rule["id"] for rule in graph_rules()}
        topic_rule_ids = {rule["id"] for rule in topic_rules()}
        self.assertIn("scope_correction_derivations", graph_rule_ids)
        self.assertIn("focus_shift_derivations", graph_rule_ids)
        self.assertIn("topic_priority", topic_rule_ids)
        self.assertIn("fallback", topic_rule_ids)


if __name__ == "__main__":
    unittest.main()