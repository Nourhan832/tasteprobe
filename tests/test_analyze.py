import json
import tempfile
import unittest
from pathlib import Path
from analyze import summarize


class AnalyzeTests(unittest.TestCase):
    def test_valid_invalid_and_duplicate(self):
        with tempfile.TemporaryDirectory() as folder:
            base = {"schema_version": 1, "next": {"action": "recommend"}, "source": "qloo-live",
                    "method": "adaptive", "recommendations": [{"entity_id": "a"}],
                    "ratings": {"a": 4}, "history": [{}, {}, {}]}
            paths = []
            for name, data in (("one.json", base), ("duplicate.json", base),
                               ("invalid.json", {**base, "ratings": {"a": 9}})):
                path = Path(folder)/name
                path.write_text(json.dumps(data))
                paths.append(path)
            result = summarize(paths)
            self.assertEqual(result["summary"][0]["rated_sessions"], 1)
            self.assertEqual(result["summary"][0]["mean_session_rating"], 4)
            self.assertEqual(len(result["warnings"]), 2)
