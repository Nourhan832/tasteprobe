import time
import unittest
from unittest.mock import patch
from service import Service


class FakeQloo:
    def __init__(self):
        self.audit = []

    def search(self, query, kind):
        return {"results": [{"entity_id": "seed1", "name": "Anchor One"},
                            {"entity_id": "seed2", "name": "Anchor Two"}]}

    def insights(self, seeds, take=50):
        self.audit.append({"source": "mock-qloo", "seeds": seeds})
        ids = ["a", "b", "c", "d", "e"]
        if seeds == ["seed2"]:
            ids.reverse()
        return {"results": {"entities": [{"entity_id": i, "name": "Film "+i} for i in ids]}}


class ServiceTests(unittest.TestCase):
    def test_full_session_and_delete(self):
        service = Service()
        state = service.create()
        identifier = state["session_id"]
        asked = []
        for answer in ("like", "skip", "dislike"):
            asked.append(state["next"]["entity_id"])
            before = state["weights"]
            state = service.answer(identifier, asked[-1], answer)
            if answer == "skip":
                self.assertEqual(before, state["weights"])
        self.assertEqual(state["next"]["action"], "recommend")
        self.assertFalse(set(asked) & {r["entity_id"] for r in state["recommendations"]})
        service.delete(identifier)
        with self.assertRaises(LookupError):
            service.state(identifier)

    def test_current_question_required(self):
        service = Service()
        state = service.create()
        with self.assertRaises(ValueError):
            service.answer(state["session_id"], "not-current", "like")
        self.assertEqual(service.state(state["session_id"])["answered"], 0)

    def test_live_requires_search_confirmation(self):
        service = Service(FakeQloo)
        with self.assertRaises(ValueError):
            service.create("live", ["seed1", "seed2"])
        service.search("anchor", "movie")
        state = service.create("live", ["seed1", "seed2"])
        self.assertEqual(state["source"], "qloo-live")
        self.assertEqual(state["evidence_coverage"]["shared_candidates"], 5)
        self.assertEqual(len(state["retrieval"]), 2)

    def test_expiry_and_capacity(self):
        service = Service(max_sessions=1, ttl=1)
        state = service.create()
        with self.assertRaises(RuntimeError):
            service.create()
        service.sessions[state["session_id"]].created -= 2
        with self.assertRaises(LookupError):
            service.state(state["session_id"])
        self.assertEqual(service.create()["answered"], 0)

    def test_each_study_strategy(self):
        for method in ("adaptive", "fixed", "random", "immediate"):
            with self.subTest(method=method), patch("service.secrets.choice", return_value=method):
                service = Service()
                state = service.create(study=True)
                count = 0
                while state["next"]["action"] == "ask":
                    state = service.answer(state["session_id"], state["next"]["entity_id"], "like")
                    count += 1
                self.assertEqual(count, 0 if method == "immediate" else 3)
                self.assertEqual(state["method"], method)

    def test_upstream_failure_does_not_become_demo(self):
        class Broken(FakeQloo):
            def insights(self, *args, **kwargs):
                raise TimeoutError("upstream timeout")
        service = Service(Broken)
        service.search("anchor", "movie")
        with self.assertRaises(TimeoutError):
            service.create("live", ["seed1", "seed2"])
        self.assertFalse(service.sessions)
