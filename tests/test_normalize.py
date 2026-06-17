import unittest

from ts_lang.normalize import normalize_utterance


class NormalizeTests(unittest.TestCase):
    def test_lowercases_and_tokenizes(self) -> None:
        utterance = normalize_utterance("NAH bro FUCKING STOP")
        self.assertEqual(utterance.clean, "nah bro fucking stop")
        self.assertEqual(utterance.tokens[:3], ["nah", "bro", "fucking"])

    def test_detects_frustration_markers(self) -> None:
        utterance = normalize_utterance("nah bro fucking stop")
        self.assertTrue(utterance.markers.frustration)
        self.assertTrue(utterance.markers.negation)
        self.assertGreater(utterance.markers.intensity, 0.5)

    def test_collapses_whitespace(self) -> None:
        utterance = normalize_utterance("  hello   world  ")
        self.assertEqual(utterance.clean, "hello world")


if __name__ == "__main__":
    unittest.main()