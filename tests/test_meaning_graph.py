import unittest

from ts_lang.compiler import compile_utterance
from ts_lang.meaning_graph import build_meaning_graph
from ts_lang.types import DialogueActResult, SemanticFrame


class MeaningGraphTests(unittest.TestCase):
    def test_builds_root_and_frame_nodes_with_provenance(self) -> None:
        act = DialogueActResult(
            act="correct_assistant",
            meaning={"matched_phrases": ["nah bro", "same usability"]},
            confidence=0.95,
        )
        frames = [
            SemanticFrame(
                schema="usability_target",
                slots={"target": "usability_parity", "desired_focus": "chatbot_usability"},
                provenance={"source_type": "frame_builder", "source_id": "usability_frame", "pattern": "same_usability"},
            )
        ]
        graph = build_meaning_graph(
            dialogue_act=act.act,
            subact=None,
            act_result=act,
            frames=frames,
            topic="usability",
        )

        self.assertEqual(graph.root_node_id, "node_act_root")
        self.assertGreaterEqual(len(graph.nodes), 2)
        self.assertGreaterEqual(len(graph.edges), 1)

        root = graph.nodes[0]
        self.assertEqual(root.kind, "dialogue_act")
        self.assertEqual(root.provenance["source_type"], "dialogue_act")
        self.assertEqual(root.provenance["matched_phrases"], ["nah bro", "same usability"])

        frame_node = next(n for n in graph.nodes if n.kind == "usability_target")
        self.assertEqual(frame_node.provenance["pattern"], "same_usability")
        self.assertEqual(frame_node.slots["desired_focus"], "chatbot_usability")

        expresses = next(e for e in graph.edges if e.relation == "expresses")
        self.assertEqual(expresses.source_id, "node_act_root")
        self.assertEqual(expresses.target_id, frame_node.node_id)

    def test_scope_correction_derives_reject_and_accept_nodes(self) -> None:
        act = DialogueActResult(act="correct_assistant", meaning={}, confidence=0.9)
        frames = [
            SemanticFrame(
                schema="scope_correction",
                slots={
                    "rejects": ["architecture_parity"],
                    "accepts": ["chatbot_usability"],
                    "desired_focus": "chatbot_usability",
                },
                provenance={"source_type": "frame_builder", "source_id": "scope_frame"},
            )
        ]
        graph = build_meaning_graph(
            dialogue_act=act.act,
            subact=None,
            act_result=act,
            frames=frames,
            topic="chatbot",
        )

        reject_nodes = [n for n in graph.nodes if n.kind == "rejected_scope"]
        accept_nodes = [n for n in graph.nodes if n.kind == "accepted_scope"]
        self.assertEqual(len(reject_nodes), 1)
        self.assertEqual(len(accept_nodes), 1)
        self.assertTrue(any(e.relation == "rejects" for e in graph.edges))
        self.assertTrue(any(e.relation == "accepts" for e in graph.edges))

    def test_desired_focus_helper_reads_frame_slots(self) -> None:
        turn = compile_utterance("nah bro we just want the same usability")
        focus = turn.meaning_graph.desired_focus()
        self.assertEqual(focus, "chatbot_usability")

    def test_golden_usability_utterance_graph(self) -> None:
        turn = compile_utterance("nah bro we just want the same usability")
        graph = turn.meaning_graph

        self.assertEqual(turn.dialogue_act, "correct_assistant")
        kinds = {n.kind for n in graph.nodes}
        self.assertIn("dialogue_act", kinds)
        self.assertIn("usability_target", kinds)
        self.assertTrue(graph.to_dict()["node_count"] >= 2)

        root = next(n for n in graph.nodes if n.kind == "dialogue_act")
        self.assertIn("same usability", root.provenance.get("matched_phrases", []))

        reject_nodes = [n for n in graph.nodes if n.kind == "rejected_scope"]
        self.assertTrue(reject_nodes)
        self.assertEqual(reject_nodes[0].label, "architecture_parity")
        self.assertEqual(reject_nodes[0].slots["value"], "architecture_parity")

    def test_golden_strategic_redirect_graph(self) -> None:
        turn = compile_utterance(
            "nah, im pretty sure we now have the reasoning engine pretty solid"
        )
        graph = turn.meaning_graph

        self.assertEqual(turn.dialogue_act, "strategic_redirect")
        kinds = {n.kind for n in graph.nodes}
        self.assertIn("focus_shift", kinds)
        self.assertTrue(any(e.relation == "shifts_to" for e in graph.edges))
        self.assertEqual(graph.desired_focus(), "chatbot_language_layer")

    def test_golden_next_step_graph(self) -> None:
        turn = compile_utterance("what is next")
        graph = turn.meaning_graph

        self.assertEqual(turn.dialogue_act, "ask_for_next_step")
        root = next(n for n in graph.nodes if n.kind == "dialogue_act")
        self.assertIn("what is next", root.provenance.get("matched_phrases", []))


if __name__ == "__main__":
    unittest.main()