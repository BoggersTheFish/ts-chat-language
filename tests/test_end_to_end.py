import unittest

from chat.session import TSChatSession


class EndToEndTests(unittest.TestCase):
    def test_correction_reframe_flow(self) -> None:
        session = TSChatSession()
        receipt = session.handle("nah bro we just want the same usability")
        self.assertEqual(receipt.compiled_turn.dialogue_act, "correct_assistant")
        self.assertIn("usability parity", receipt.rendered_reply.text.lower())

    def test_strategic_redirect_flow(self) -> None:
        session = TSChatSession()
        receipt = session.handle(
            "nah, im pretty sure we now have the reasoning engine pretty solid"
        )
        self.assertEqual(receipt.compiled_turn.dialogue_act, "strategic_redirect")
        self.assertIn("language", receipt.rendered_reply.text.lower())

    def test_frustration_flow(self) -> None:
        session = TSChatSession()
        receipt = session.handle("nah bro FUCKING STOP")
        self.assertIn(receipt.compiled_turn.dialogue_act, {"express_frustration", "reject_framing", "correct_assistant"})
        self.assertTrue(receipt.rendered_reply.text)

    def test_next_step_plan_flow(self) -> None:
        session = TSChatSession()
        receipt = session.handle("what is next")
        self.assertEqual(receipt.compiled_turn.dialogue_act, "ask_for_next_step")
        self.assertIn("normalizer", receipt.rendered_reply.text.lower())

    def test_continue_topic_across_turns(self) -> None:
        session = TSChatSession()
        session.handle("build the language compiler for the chatbot")
        receipt = session.handle("also we need conversation memory")
        self.assertTrue(session.state.turn_history)
        self.assertTrue(receipt.rendered_reply.text)

    def test_confirm_direction(self) -> None:
        session = TSChatSession()
        receipt = session.handle("yes that's exactly the actual target")
        self.assertIn(receipt.compiled_turn.dialogue_act, {"confirm_direction", "strategic_redirect", "correct_assistant"})


if __name__ == "__main__":
    unittest.main()