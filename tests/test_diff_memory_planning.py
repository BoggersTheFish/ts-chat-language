import unittest

from chat.session import TSChatSession
from ts_render.response_plan import plan_response
from ts_state.conversation import ConversationState
from ts_state.diff_memory import build_diff_memory


class DiffMemoryPlanningTests(unittest.TestCase):
    def test_first_turn_has_no_memory_context(self) -> None:
        session = TSChatSession()
        receipt = session.handle("nah bro we just want the same usability")
        self.assertEqual(receipt.response_plan.slots.get("memory_context"), "")
        self.assertNotIn("already ruled out", receipt.rendered_reply.text.lower())

    def test_second_turn_planner_uses_prior_rejects_and_focus_shift(self) -> None:
        session = TSChatSession()
        session.handle("nah bro we just want the same usability")
        receipt = session.handle(
            "nah, im pretty sure we now have the reasoning engine pretty solid"
        )

        self.assertIn("already ruled out", receipt.rendered_reply.text.lower())
        self.assertIn("architecture parity", receipt.rendered_reply.text.lower())
        self.assertIn("shifting focus", receipt.rendered_reply.text.lower())
        self.assertEqual(
            receipt.response_plan.template_id,
            "confirm_shift_with_memory",
        )
        self.assertTrue(receipt.response_plan.slots.get("memory_context"))

    def test_third_turn_plan_references_accumulated_memory(self) -> None:
        session = TSChatSession()
        session.handle("nah bro we just want the same usability")
        session.handle(
            "nah, im pretty sure we now have the reasoning engine pretty solid"
        )
        receipt = session.handle("what is next")

        self.assertEqual(receipt.response_plan.template_id, "provide_plan_with_memory")
        text = receipt.rendered_reply.text.lower()
        self.assertIn("already ruled out", text)
        self.assertIn("plan for", text)

    def test_planner_works_from_diff_memory_without_semantic_frames(self) -> None:
        session = TSChatSession()
        session.handle("nah bro we just want the same usability")
        turn = session.handle(
            "nah, im pretty sure we now have the reasoning engine pretty solid"
        ).compiled_turn

        graph_only = turn.__class__(
            raw=turn.raw,
            normalized=turn.normalized,
            dialogue_act=turn.dialogue_act,
            subact=turn.subact,
            semantic_frames=[],
            meaning_graph=turn.meaning_graph,
            emotion=turn.emotion,
            topic=turn.topic,
            confidence=turn.confidence,
            ambiguities=turn.ambiguities,
            status=turn.status,
            repair_action=turn.repair_action,
            known_terms=turn.known_terms,
            unknown_terms=turn.unknown_terms,
        )
        plan = plan_response(graph_only, session.state)
        self.assertIn("already ruled out", plan.main_point.lower())
        self.assertEqual(plan.template_id, "confirm_shift_with_memory")


if __name__ == "__main__":
    unittest.main()