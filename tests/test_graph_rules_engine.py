import unittest

from ts_lang.graph_rules import apply_graph_derivations
from ts_lang.meaning_graph import _GraphBuilder
from ts_lang.resources import graph_rules, reload_resources
from ts_lang.types import SemanticFrame
from ts_packs.loader import reset_registry_cache


class GraphRulesEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_registry_cache()
        reload_resources()

    def test_scope_correction_derivations_from_pack_rules(self) -> None:
        builder = _GraphBuilder()
        frame = SemanticFrame(
            schema="scope_correction",
            slots={
                "rejects": ["architecture_parity"],
                "accepts": ["chatbot_usability"],
            },
            provenance={"source_type": "frame_builder", "source_id": "scope_frame"},
        )
        frame_node_id = "node_frame_scope_correction_scope_frame"
        fired = apply_graph_derivations(
            builder,
            frame=frame,
            frame_node_id=frame_node_id,
            frame_provenance=frame.provenance,
            rules=graph_rules(),
        )

        self.assertIn("scope_correction_derivations", fired)
        reject_nodes = [node for node in builder.nodes if node.kind == "rejected_scope"]
        accept_nodes = [node for node in builder.nodes if node.kind == "accepted_scope"]
        self.assertEqual(len(reject_nodes), 1)
        self.assertEqual(len(accept_nodes), 1)
        self.assertTrue(any(edge.relation == "rejects" for edge in builder.edges))
        self.assertTrue(any(edge.relation == "accepts" for edge in builder.edges))

    def test_architecture_preference_derivations_from_pack_rules(self) -> None:
        builder = _GraphBuilder()
        frame = SemanticFrame(
            schema="architecture_preference",
            slots={"avoid": ["transformer_training"], "prefer": ["language_compiler"]},
            provenance={"source_type": "frame_builder", "source_id": "arch_frame"},
        )
        fired = apply_graph_derivations(
            builder,
            frame=frame,
            frame_node_id="node_frame_architecture_preference_arch_frame",
            frame_provenance=frame.provenance,
            rules=graph_rules(),
        )

        self.assertIn("architecture_preference_derivations", fired)
        constraints = [node for node in builder.nodes if node.kind == "constraint"]
        self.assertEqual(len(constraints), 2)
        polarities = {node.slots.get("polarity") for node in constraints}
        self.assertEqual(polarities, {"avoid", "prefer"})

    def test_focus_shift_derivation_from_pack_rules(self) -> None:
        builder = _GraphBuilder()
        frame = SemanticFrame(
            schema="focus_shift",
            slots={"new_focus": "reasoning_engine"},
            provenance={"source_type": "frame_builder", "source_id": "focus_frame"},
        )
        fired = apply_graph_derivations(
            builder,
            frame=frame,
            frame_node_id="node_frame_focus_shift_focus_frame",
            frame_provenance=frame.provenance,
            rules=graph_rules(),
        )

        self.assertIn("focus_shift_derivations", fired)
        focus_nodes = [node for node in builder.nodes if node.kind == "focus_target"]
        self.assertEqual(len(focus_nodes), 1)
        self.assertEqual(focus_nodes[0].slots.get("new_focus"), "reasoning_engine")
        self.assertTrue(any(edge.relation == "shifts_to" for edge in builder.edges))


if __name__ == "__main__":
    unittest.main()