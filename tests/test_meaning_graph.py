import unittest

from ts_lang.compiler import compile_utterance
from ts_lang.meaning_graph import (
    MeaningGraph,
    MeaningNode,
    build_meaning_graph,
    is_python_repr_string,
    validate_meaning_graph,
)
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
                provenance={
                    "source_type": "frame_builder",
                    "source_id": "usability_frame",
                    "pattern": "same_usability",
                },
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
        self.assertEqual(frame_node.node_id, "node_frame_usability_target_usability_frame")
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
        self.assertEqual(reject_nodes[0].node_id, "node_rejected_scope_architecture_parity")
        self.assertEqual(accept_nodes[0].node_id, "node_accepted_scope_chatbot_usability")
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
        self.assertTrue(graph.to_dict()["validation"]["valid"])

        root = next(n for n in graph.nodes if n.kind == "dialogue_act")
        self.assertIn("same usability", root.provenance.get("matched_phrases", []))

        reject_nodes = [n for n in graph.nodes if n.kind == "rejected_scope"]
        self.assertTrue(reject_nodes)
        self.assertEqual(reject_nodes[0].label, "architecture_parity")
        self.assertEqual(reject_nodes[0].slots["value"], "architecture_parity")
        self.assertNotRegex(reject_nodes[0].node_id, r"_\d+_")

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
        focus_node = next(n for n in graph.nodes if n.kind == "focus_target")
        self.assertEqual(focus_node.node_id, "node_focus_target_chatbot_language_layer")

    def test_golden_next_step_graph(self) -> None:
        turn = compile_utterance("what is next")
        graph = turn.meaning_graph

        self.assertEqual(turn.dialogue_act, "ask_for_next_step")
        root = next(n for n in graph.nodes if n.kind == "dialogue_act")
        self.assertIn("what is next", root.provenance.get("matched_phrases", []))
        self.assertTrue(validate_meaning_graph(graph).valid)

    def test_deterministic_node_ids_independent_of_frame_order(self) -> None:
        act = DialogueActResult(act="correct_assistant", meaning={}, confidence=0.9)
        frame_a = SemanticFrame(
            schema="usability_target",
            slots={"desired_focus": "chatbot_usability"},
            provenance={"source_type": "frame_builder", "source_id": "usability_frame"},
        )
        frame_b = SemanticFrame(
            schema="scope_correction",
            slots={"rejects": ["architecture_parity"]},
            provenance={"source_type": "frame_builder", "source_id": "scope_frame"},
        )

        graph_ab = build_meaning_graph(
            dialogue_act=act.act,
            subact=None,
            act_result=act,
            frames=[frame_a, frame_b],
            topic="chatbot",
        )
        graph_ba = build_meaning_graph(
            dialogue_act=act.act,
            subact=None,
            act_result=act,
            frames=[frame_b, frame_a],
            topic="chatbot",
        )

        ids_ab = {n.node_id for n in graph_ab.nodes}
        ids_ba = {n.node_id for n in graph_ba.nodes}
        self.assertEqual(ids_ab, ids_ba)
        self.assertIn("node_frame_usability_target_usability_frame", ids_ab)
        self.assertIn("node_frame_scope_correction_scope_frame", ids_ab)

    def test_duplicate_semantic_nodes_are_deduped(self) -> None:
        act = DialogueActResult(act="correct_assistant", meaning={}, confidence=0.9)
        frames = [
            SemanticFrame(
                schema="scope_correction",
                slots={"rejects": ["architecture_parity"]},
                provenance={"source_type": "frame_builder", "source_id": "scope_frame_a"},
            ),
            SemanticFrame(
                schema="scope_correction",
                slots={"rejects": ["architecture_parity"]},
                provenance={"source_type": "frame_builder", "source_id": "scope_frame_b"},
            ),
        ]
        graph = build_meaning_graph(
            dialogue_act=act.act,
            subact=None,
            act_result=act,
            frames=frames,
            topic="chatbot",
        )

        reject_nodes = [n for n in graph.nodes if n.kind == "rejected_scope"]
        self.assertEqual(len(reject_nodes), 1)
        reject_edges = [e for e in graph.edges if e.relation == "rejects"]
        self.assertEqual(len(reject_edges), 2)
        self.assertEqual(reject_edges[0].target_id, reject_edges[1].target_id)

    def test_validate_detects_missing_edge_targets_and_repr_strings(self) -> None:
        from ts_lang.meaning_graph import MeaningEdge

        bad_graph = MeaningGraph(
            nodes=[
                MeaningNode(
                    node_id="node_a",
                    kind="rejected_scope",
                    label="['architecture_parity']",
                    slots={"value": "['architecture_parity']"},
                    provenance={"source_type": "test"},
                )
            ],
            edges=[
                MeaningEdge(
                    edge_id="edge_bad",
                    source_id="node_a",
                    target_id="node_missing",
                    relation="rejects",
                    provenance={"source_type": "test"},
                )
            ],
            root_node_id="node_a",
            summary="bad",
        )
        report = validate_meaning_graph(bad_graph)
        self.assertFalse(report.valid)
        self.assertTrue(any("python_repr" in err for err in report.errors))
        self.assertTrue(any("edge_missing_target" in err for err in report.errors))

    def test_is_python_repr_string(self) -> None:
        self.assertTrue(is_python_repr_string("['architecture_parity']"))
        self.assertFalse(is_python_repr_string("architecture_parity"))


if __name__ == "__main__":
    unittest.main()