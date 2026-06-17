import unittest

from ts_lang.dialogue_act import compile_dialogue_act
from ts_lang.normalize import normalize_utterance


class DialogueActTests(unittest.TestCase):
    def test_correction_act(self) -> None:
        utterance = normalize_utterance("nah bro we just want the same usability")
        act = compile_dialogue_act(utterance)
        self.assertEqual(act.act, "correct_assistant")

    def test_strategic_redirect(self) -> None:
        utterance = normalize_utterance(
            "nah, im pretty sure we now have the reasoning engine pretty solid"
        )
        act = compile_dialogue_act(utterance)
        self.assertEqual(act.act, "strategic_redirect")

    def test_reject_framing(self) -> None:
        utterance = normalize_utterance("no fuck off i want the chatbot too")
        act = compile_dialogue_act(utterance)
        self.assertIn(act.act, {"reject_framing", "correct_assistant", "express_frustration"})

    def test_ask_for_next_step(self) -> None:
        utterance = normalize_utterance("what is next")
        act = compile_dialogue_act(utterance)
        self.assertEqual(act.act, "ask_for_next_step")


if __name__ == "__main__":
    unittest.main()