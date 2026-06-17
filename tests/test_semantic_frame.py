import unittest

from ts_lang.dialogue_act import compile_dialogue_act
from ts_lang.normalize import normalize_utterance
from ts_lang.semantic_frame import compile_semantic_frames


class SemanticFrameTests(unittest.TestCase):
    def test_usability_frame(self) -> None:
        utterance = normalize_utterance("nah bro we just want the same usability")
        act = compile_dialogue_act(utterance)
        frames, known, _unknown = compile_semantic_frames(utterance, act)
        schemas = [f.schema for f in frames]
        self.assertIn("usability_target", schemas)
        self.assertIn("usability", known)

    def test_architecture_preference_frame(self) -> None:
        utterance = normalize_utterance("we dont need to train it on data to have language")
        act = compile_dialogue_act(utterance)
        frames, _known, _unknown = compile_semantic_frames(utterance, act)
        schemas = [f.schema for f in frames]
        self.assertIn("claim", schemas)
        self.assertIn("architecture_preference", schemas)


if __name__ == "__main__":
    unittest.main()