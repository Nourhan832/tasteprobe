import unittest
from engine import Probe
from service import Service
from test_service import FakeQloo
from stress_benchmark import run


class EvidenceTests(unittest.TestCase):
    def test_preview_does_not_mutate(self):
        p = Probe({"a": {"x": 1., "y": .4, "z": .7}, "b": {"x": 0., "y": .8, "z": .2}}, {})
        before = (list(p.weights), list(p.history), set(p.asked))
        previews = p.previews("x")
        self.assertEqual((p.weights, p.history, p.asked), before)
        self.assertEqual(previews["like"][0]["entity_id"], "z")
        self.assertEqual(previews["dislike"][0]["entity_id"], "y")

    def test_undo_replays_exactly(self):
        service = Service()
        state = service.create()
        identifier = state["session_id"]
        state = service.answer(identifier, state["next"]["entity_id"], "like")
        weights = state["weights"]
        question = state["next"]["entity_id"]
        service.answer(identifier, question, "dislike")
        undone = service.undo(identifier)
        self.assertEqual(undone["weights"], weights)
        self.assertEqual(undone["next"]["entity_id"], question)
        self.assertEqual(undone["undo_count"], 1)

    def test_research_disables_answer_editing_and_preview(self):
        service = Service()
        state = service.create(study=True)
        self.assertNotIn("answer_previews", state["next"])
        with self.assertRaises(ValueError):
            service.undo(state["session_id"])

    def test_anchor_evidence_is_not_overwritten(self):
        service = Service(FakeQloo)
        service.search("anchor", "movie")
        state = service.create("live", ["seed1", "seed2"])
        evidence = state["recommendations"][0]["evidence"]
        self.assertEqual(len(evidence), 2)
        for item in evidence.values():
            self.assertEqual(item["source"], "qloo-live")
            self.assertIn("returned_rank", item)

    def test_stress_benchmark_is_reproducible_and_heldout(self):
        a, b = run(trials=5), run(trials=5)
        self.assertEqual(a, b)
        self.assertEqual(a["disjoint_evaluation_candidates"], 12)
        self.assertEqual(set(a["scenarios"]), {"matched", "mixed_tastes", "reversed_tastes", "frequent_skips"})
        for scenario in a["scenarios"].values():
            for method in scenario["methods"].values():
                self.assertGreaterEqual(method["mean_regret"], 0)
