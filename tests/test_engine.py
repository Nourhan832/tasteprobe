import unittest
from engine import Probe, entropy
from qloo import rank_profile


class EngineTests(unittest.TestCase):
    def make(self, budget=3):
        return Probe({"a": {"x": 1., "y": .5, "z": 0.},
                      "b": {"x": 0., "y": .5, "z": 1.}}, {}, budget)

    def test_informative_question_selected(self):
        p = self.make()
        self.assertEqual(p.next_question()["entity_id"], "x")
        self.assertGreater(p.gain("x"), p.gain("y"))

    def test_answer_updates_normalized_weights(self):
        p = self.make()
        p.answer("x", "like")
        self.assertGreater(p.weights[0], p.weights[1])
        self.assertAlmostEqual(sum(p.weights), 1.)
        self.assertLess(entropy(p.weights), 1.)

    def test_skip_does_not_change_model(self):
        p = self.make()
        p.answer("x", "skip")
        self.assertEqual(p.weights, [.5, .5])
        self.assertNotIn("x", [r["entity_id"] for r in p.recommendations()])

    def test_budget_enforced(self):
        p = self.make(1)
        p.answer("x", "like")
        self.assertEqual(p.next_question()["action"], "recommend")
        with self.assertRaises(ValueError):
            p.answer("z", "like")

    def test_missing_evidence_not_imputed(self):
        p = Probe({"a": {"x": 1.}, "b": {"y": 1.}}, {})
        self.assertEqual(p.next_question()["action"], "recommend")
        self.assertEqual(p.recommendations(), [])
        with self.assertRaises(ValueError):
            p.answer("x", "like")

    def test_identical_profiles_stop(self):
        p = Probe({"a": {"x": .5}, "b": {"x": .5}}, {})
        self.assertEqual(p.next_question()["action"], "recommend")

    def test_bad_utilities_rejected(self):
        for value in (float("nan"), float("inf"), -1, 2):
            with self.assertRaises(ValueError):
                Probe({"a": {"x": value}}, {})

    def test_schema_and_order(self):
        profile, _ = rank_profile({"results": {"entities": [
            {"entity_id": "a", "name": "A"}, {"entity_id": "b", "name": "B"}]}})
        self.assertEqual(profile, {"a": 1., "b": 0.})
        with self.assertRaises(ValueError):
            rank_profile({"results": []})


if __name__ == "__main__":
    unittest.main()
