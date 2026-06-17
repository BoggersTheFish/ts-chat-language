import unittest

from ts_lang.dialogue_act import compile_dialogue_act
from ts_lang.normalize import normalize_utterance
from ts_lang.semantic_frame import compile_semantic_frames
from ts_lang.slot_normalize import extend_slot_values, normalize_string_list
from ts_lang.types import SemanticFrame
from ts_lang.slot_normalize import normalize_frame_slots


class SlotNormalizeTests(unittest.TestCase):
    def test_extend_slot_values_flattens_lists(self) -> None:
        target: list[str] = []
        extend_slot_values(target, ["architecture_parity"])
        extend_slot_values(target, "chatbot_usability")
        extend_slot_values(target, ["architecture_parity", "transformer_internals"])
        self.assertEqual(
            target,
            ["architecture_parity", "chatbot_usability", "transformer_internals"],
        )

    def test_normalize_string_list_dedupes(self) -> None:
        self.assertEqual(
            normalize_string_list(["a", "a", "b"]),
            ["a", "b"],
        )

    def test_normalize_frame_slots_for_scope_correction(self) -> None:
        frame = SemanticFrame(
            schema="scope_correction",
            slots={"rejects": ["architecture_parity"], "accepts": "chatbot"},
            provenance={"source_type": "frame_builder", "source_id": "scope_frame"},
        )
        normalized = normalize_frame_slots(frame)
        self.assertEqual(normalized.slots["rejects"], ["architecture_parity"])
        self.assertEqual(normalized.slots["accepts"], ["chatbot"])

    def test_scope_frame_from_golden_utterance_uses_clean_lists(self) -> None:
        utterance = normalize_utterance("nah bro we just want the same usability")
        act = compile_dialogue_act(utterance)
        frames, _known, _unknown = compile_semantic_frames(utterance, act)
        scope = next(f for f in frames if f.schema == "scope_correction")
        self.assertEqual(scope.slots["rejects"], ["architecture_parity"])
        for value in scope.slots["rejects"]:
            self.assertNotIn("[", value)


if __name__ == "__main__":
    unittest.main()