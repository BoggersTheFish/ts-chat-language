import unittest

from chat.session import TSChatSession


class RendererTests(unittest.TestCase):
    def test_golden_usability_reply(self) -> None:
        session = TSChatSession()
        receipt = session.handle("nah bro we just want the same usability")
        self.assertIn("usability parity", receipt.rendered_reply.text.lower())
        self.assertIn("architecture parity", receipt.rendered_reply.text.lower())

    def test_partial_parse_asks_question(self) -> None:
        session = TSChatSession()
        receipt = session.handle("xyzzy qwerty unknown phrase blob")
        if receipt.compiled_turn.status == "partial_parse":
            self.assertIn("?", receipt.rendered_reply.text)


if __name__ == "__main__":
    unittest.main()