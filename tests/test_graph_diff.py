import unittest

from chat.session import TSChatSession
from ts_lang.compiler import compile_utterance
from ts_lang.graph_diff import diff_meaning_graphs


class GraphDiffTests(unittest.TestCase):
    def test_first_turn_diff_marks_nodes_as_added(self) -> None:
        session = TSChatSession()
        receipt = session.handle("nah bro we just want the same usability")
        diff = receipt.graph_diff

        self.assertIsNotNone(diff)
        self.assertIsNone(diff.previous_turn_id)
        self.assertEqual(diff.current_turn_id, 1)
        self.assertTrue(diff.added_nodes)
        self.assertFalse(diff.removed_nodes)
        self.assertIn("architecture_parity", diff.rejects_added)
        self.assertEqual(diff.focus_change["current"], "chatbot_usability")

    def test_second_turn_reports_focus_and_act_change(self) -> None:
        session = TSChatSession()
        session.handle("nah bro we just want the same usability")
        receipt = session.handle(
            "nah, im pretty sure we now have the reasoning engine pretty solid"
        )
        diff = receipt.graph_diff

        self.assertEqual(diff.previous_turn_id, 1)
        self.assertEqual(diff.current_turn_id, 2)
        self.assertEqual(
            diff.dialogue_act_change["previous"],
            "correct_assistant",
        )
        self.assertEqual(diff.dialogue_act_change["current"], "strategic_redirect")
        self.assertEqual(diff.focus_change["previous"], "chatbot_usability")
        self.assertEqual(diff.focus_change["current"], "chatbot_language_layer")
        self.assertTrue(any(node.kind == "focus_shift" for node in diff.added_nodes))
        self.assertIn("focus", diff.summary)

    def test_demo_script_accumulates_graph_diff_in_history(self) -> None:
        session = TSChatSession()
        for text in [
            "nah bro we just want the same usability",
            "nah, im pretty sure we now have the reasoning engine pretty solid",
            "what is next",
        ]:
            session.handle(text)

        self.assertEqual(len(session.state.turn_history), 3)
        self.assertTrue(session.state.turn_history[0].graph_diff)
        self.assertTrue(session.state.turn_history[1].graph_diff)
        self.assertIn(
            "strategic_redirect",
            session.state.turn_history[1].graph_diff["dialogue_act_change"]["current"],
        )
        self.assertEqual(
            session.state.turn_history[2].graph_diff["dialogue_act_change"]["current"],
            "ask_for_next_step",
        )

    def test_diff_is_deterministic_for_same_graph_pair(self) -> None:
        first = compile_utterance("nah bro we just want the same usability")
        second = compile_utterance(
            "nah, im pretty sure we now have the reasoning engine pretty solid",
            None,
        )
        diff_a = diff_meaning_graphs(
            first.meaning_graph,
            second.meaning_graph,
            previous_turn_id=1,
            current_turn_id=2,
        )
        diff_b = diff_meaning_graphs(
            first.meaning_graph,
            second.meaning_graph,
            previous_turn_id=1,
            current_turn_id=2,
        )
        self.assertEqual(diff_a.to_dict(), diff_b.to_dict())

    def test_receipt_serializes_graph_diff(self) -> None:
        session = TSChatSession()
        receipt = session.handle("what is next")
        payload = receipt.to_dict()
        self.assertIn("graph_diff", payload)
        self.assertEqual(payload["graph_diff"]["current_turn_id"], 1)
        self.assertIn("summary", payload["graph_diff"])


if __name__ == "__main__":
    unittest.main()