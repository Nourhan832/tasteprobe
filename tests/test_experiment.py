import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from service import Service
from analyze_paired import summarize


class PairedTests(unittest.TestCase):
    def complete(self):
        service = Service()
        state = service.create(experiment=True, consent=True)
        identifier = state["session_id"]
        asked = set()
        while state["next"]["action"] == "ask":
            self.assertNotIn("answer_previews", state["next"])
            asked.add(state["next"]["entity_id"])
            state = service.answer(identifier, state["next"]["entity_id"], "like")
        self.assertFalse(asked & {r["entity_id"] for r in state["recommendations"]})
        self.assertEqual(set(state["paired_results"]), {"adaptive", "fixed"})
        self.assertLessEqual(state["answered"], 6)
        return state

    def test_explicit_consent_before_network_calls(self):
        factory = unittest.mock.Mock()
        service = Service(factory)
        with self.assertRaises(ValueError):
            service.create("live", ["a", "b"], experiment=True)
        factory.assert_not_called()

    def test_frozen_evidence_and_unasked_holdout(self):
        state = self.complete()
        self.assertTrue(state["consent"]["confirmed"])
        self.assertGreaterEqual(state["evidence_coverage"]["holdout_pool"], 3)

    def test_both_round_orders_and_duplicate_exports(self):
        state = self.complete()
        state.pop("session_id")
        state.update(schema_version=2, ratings={r["entity_id"]: 4 for r in state["recommendations"]})
        with tempfile.TemporaryDirectory() as directory:
            a, b = Path(directory)/"a.json", Path(directory)/"b.json"
            a.write_text(json.dumps(state)); b.write_text(json.dumps({**state, "exported_at": "different"}))
            result = summarize([a, b])
            self.assertEqual(result["summary"][0]["paired_sessions"], 1)
            self.assertEqual(result["summary"][0]["mean_adaptive_minus_fixed_rating"], 0)
            self.assertEqual(len(result["warnings"]), 1)
            state["qa_context"] = {"type": "scripted"}
            a.write_text(json.dumps(state))
            self.assertEqual(summarize([a])["summary"], [])
