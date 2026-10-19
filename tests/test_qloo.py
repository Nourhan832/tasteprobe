import os
import subprocess
import unittest
from unittest.mock import patch
from qloo import Qloo


class QlooTests(unittest.TestCase):
    def environment(self, extra=None):
        return patch.dict(os.environ, {"QLOO_API_KEY": "test-only-not-a-real-key", "QLOO_TRANSPORT": "harness",
                                      "QLOO_API_HOST": "https://api.qloo.com", **(extra or {})}, clear=True)

    def test_harness_search_keeps_key_out_of_arguments(self):
        with self.environment(), patch("qloo.shutil.which", return_value="/usr/bin/qloo"), patch("qloo.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, '[{"entity_id":"x","name":"X"}]', '')
            data = Qloo().search("a query; not a shell", "movie")
            args = run.call_args.args[0]
            self.assertEqual(args[:3], ["/usr/bin/qloo", "api", "search"])
            self.assertNotIn("test-only-not-a-real-key", " ".join(args))
            self.assertFalse(run.call_args.kwargs["shell"])
            self.assertEqual(data["results"][0]["name"], "X")

    def test_upstream_errors_do_not_expose_output(self):
        with self.environment(), patch("qloo.shutil.which", return_value="/usr/bin/qloo"), patch("qloo.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess([], 1, '', 'private diagnostic')
            with self.assertRaises(RuntimeError) as ctx:
                Qloo().search("x")
            self.assertNotIn("private diagnostic", str(ctx.exception))

    def test_invalid_origin_and_seed(self):
        with self.environment({"QLOO_API_HOST": "https://attacker.example"}):
            with self.assertRaises(ValueError):
                Qloo()
        with self.environment():
            with self.assertRaises(ValueError):
                Qloo().insights(["not-a-uuid"])
