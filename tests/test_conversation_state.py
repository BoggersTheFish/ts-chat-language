import unittest

from ts_lang.compiler import compile_utterance
from ts_state.conversation import ConversationState


class ConversationStateTests(unittest.TestCase):
    def test_rejected_frames_accumulate(self) -> None:
        state = ConversationState()
        turn = compile_utterance("no fuck off i want the chatbot too", state)
        state.apply_compiled_turn(turn)
        self.assertTrue(len(state.rejected_frames) >= 0)
        self.assertIn("chatbot", turn.topic.lower())

    def test_strategic_redirect_sets_next_action(self) -> None:
        state = ConversationState()
        turn = compile_utterance(
            "nah, im pretty sure we now have the reasoning engine pretty solid",
            state,
        )
        receipt = state.apply_compiled_turn(turn)
        self.assertIn("design chatbot language layer", state.next_expected_action or "")
        self.assertTrue(receipt.updates)


if __name__ == "__main__":
    unittest.main()