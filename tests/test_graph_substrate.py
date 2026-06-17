import unittest

from ts_lang.compiler import compile_utterance
from ts_lang.graph_queries import (
    acceptable_frame_nodes,
    rejected_scopes,
)
from ts_lang.types import CompiledTurn
from ts_render.response_plan import plan_response
from ts_state.conversation import ConversationState


class GraphSubstrateTests(unittest.TestCase):
    def test_state_rejects_derived_from_graph_nodes(self) -> None:
        state = ConversationState()
        turn = compile_utterance("nah bro we just want the same usability", state)
        self.assertIn("architecture_parity", rejected_scopes(turn.meaning_graph))
        state.apply_compiled_turn(turn)
        self.assertIn("architecture_parity", state.rejected_frames)

    def test_state_accepts_graph_frame_nodes_not_semantic_frames(self) -> None:
        state = ConversationState()
        turn = compile_utterance("nah bro we just want the same usability", state)
        state.apply_compiled_turn(turn)
        self.assertTrue(state.accepted_frames)
        for entry in state.accepted_frames:
            self.assertIn("node_id", entry)
            self.assertIn("kind", entry)
            self.assertIn(entry["kind"], {"scope_correction", "usability_target", "claim", "focus_shift"})
        graph_kinds = {n.kind for n in acceptable_frame_nodes(turn.meaning_graph)}
        accepted_kinds = {entry["kind"] for entry in state.accepted_frames}
        self.assertTrue(accepted_kinds.issubset(graph_kinds))

    def test_planner_works_when_semantic_frames_empty(self) -> None:
        turn = compile_utterance("nah bro we just want the same usability")
        graph_only = CompiledTurn(
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
        state = ConversationState()
        plan = plan_response(graph_only, state)
        self.assertIn("usability parity", plan.main_point.lower())
        self.assertEqual(plan.template_id, "ack_correction_reframe_usability")

    def test_end_to_end_golden_outputs_unchanged(self) -> None:
        from chat.session import TSChatSession

        session = TSChatSession()
        receipt = session.handle("nah bro we just want the same usability")
        self.assertIn("usability parity", receipt.rendered_reply.text.lower())
        self.assertIn("architecture parity", receipt.rendered_reply.text.lower())


if __name__ == "__main__":
    unittest.main()