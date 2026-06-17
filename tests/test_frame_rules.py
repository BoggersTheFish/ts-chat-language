import unittest

from ts_lang.compiler import compile_utterance
from ts_lang.dialogue_act import compile_dialogue_act
from ts_lang.frame_rules import evaluate_frame_rules
from ts_lang.normalize import normalize_utterance
from ts_lang.resources import reload_resources, semantic_rules
from ts_packs.loader import reset_registry_cache


class FrameRuleTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_registry_cache()
        reload_resources()

    def test_usability_rule_fires(self) -> None:
        turn = compile_utterance("nah bro we just want the same usability")
        schemas = [frame.schema for frame in turn.semantic_frames]
        self.assertIn("usability_target", schemas)
        fired = [
            frame.provenance.get("rule_id")
            for frame in turn.semantic_frames
            if frame.provenance.get("rule_id")
        ]
        self.assertIn("usability_target", fired)

    def test_architecture_preference_coalesces(self) -> None:
        turn = compile_utterance("we want chatbot usability with a language compiler not transformer training")
        arch = next(
            (frame for frame in turn.semantic_frames if frame.schema == "architecture_preference"),
            None,
        )
        self.assertIsNotNone(arch)
        self.assertTrue(arch.slots.get("avoid"))
        self.assertTrue(arch.slots.get("prefer"))

    def test_scope_and_focus_rules_on_strategic_redirect(self) -> None:
        turn = compile_utterance(
            "nah, im pretty sure we now have the reasoning engine pretty solid"
        )
        schemas = {frame.schema for frame in turn.semantic_frames}
        self.assertIn("focus_shift", schemas)
        self.assertIn("scope_correction", schemas)

    def test_no_training_rule_provenance(self) -> None:
        utterance = normalize_utterance("we dont need to train it on data to have language")
        act = compile_dialogue_act(utterance)
        frames, fired = evaluate_frame_rules(semantic_rules(), utterance, act)
        claim = next((frame for frame in frames if frame.schema == "claim"), None)
        self.assertIsNotNone(claim)
        self.assertEqual(claim.provenance.get("rule_id"), "no_training_required")
        self.assertIn("no_training_required", fired)

    def test_emotion_rule_from_base_pack(self) -> None:
        utterance = normalize_utterance("nah bro FUCKING STOP")
        act = compile_dialogue_act(utterance)
        frames, fired = evaluate_frame_rules(semantic_rules(), utterance, act)
        self.assertIn("emotion_frame", [frame.schema for frame in frames])
        self.assertIn("emotion_frame", fired)


if __name__ == "__main__":
    unittest.main()