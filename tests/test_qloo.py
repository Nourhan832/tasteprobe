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
            client = Qloo()
            data = client.search("a query; not a shell", "movie")
            args = run.call_args.args[0]
            self.assertEqual(args[:3], ["/usr/bin/qloo", "api", "search"])
            self.assertNotIn("test-only-not-a-real-key", " ".join(args))
            self.assertFalse(run.call_args.kwargs["shell"])
            self.assertEqual(run.call_args.kwargs["env"]["QLOO_BASE_URL"], "https://api.qloo.com")
            self.assertEqual(run.call_args.kwargs["env"]["QLOO_TRUSTED_BASE_URL"], "https://api.qloo.com")
            self.assertEqual(data["results"][0]["name"], "X")
            self.assertIn("retrieved_at", client.audit[0])
            self.assertGreaterEqual(client.audit[0]["duration_ms"], 0)

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

    def test_hackathon_host_is_trusted_only_after_allowlist_validation(self):
        with self.environment({"QLOO_API_HOST": "https://hackathon.api.qloo.com"}), patch("qloo.shutil.which", return_value="/usr/bin/qloo"), patch("qloo.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, '[]', '')
            Qloo().search("x")
            self.assertEqual(run.call_args.kwargs["env"]["QLOO_TRUSTED_BASE_URL"], "https://hackathon.api.qloo.com")

    def test_safe_auth_diagnostic_excludes_upstream_message(self):
        with self.environment(), patch("qloo.shutil.which", return_value="/usr/bin/qloo"), patch("qloo.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess([], 3, '{"error":true,"code":"AUTH_FAILED","message":"private diagnostic"}', '')
            with self.assertRaises(RuntimeError) as ctx:
                Qloo().search("x")
            self.assertIn("AUTH_FAILED", str(ctx.exception))
            self.assertNotIn("private diagnostic", str(ctx.exception))

    def test_insights_requests_only_fields_used_by_the_policy(self):
        with self.environment(), patch("qloo.shutil.which", return_value="/usr/bin/qloo"), patch("qloo.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, '[{"entity_id":"x","name":"X"}]', '')
            Qloo().insights(["00000000-0000-0000-0000-000000000001"])
            args = run.call_args.args[0]
            self.assertIn("--fields", args)
            self.assertEqual(args[args.index("--fields")+1], "entity_id,name,properties.description,properties.release_year")
            self.assertNotIn("--params", args)

    def test_rich_event_payload_is_discarded_after_parsing(self):
        import json
        payload = [{"entity_id": "x", "name": "X", "unused": "a"*2_100_000}]
        with self.environment(), patch("qloo.shutil.which", return_value="/usr/bin/qloo"), patch("qloo.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, json.dumps(payload), '')
            client = Qloo()
            self.assertEqual(client.search("x"), {"results": [{"entity_id": "x", "name": "X"}]})
            self.assertGreater(client.audit[0]["upstream_response_characters"], 2_000_000)

    def test_display_metadata_is_bounded_and_source_provided(self):
        from qloo import compact_entity
        item = compact_entity({"entity_id": "x", "name": "X", "properties": {
            "description": "a"*2000, "release_year": "1999", "unused": "not retained"}})
        self.assertEqual(len(item["properties"]["description"]), 1200)
        self.assertEqual(item["properties"]["release_year"], 1999)
        self.assertNotIn("unused", item["properties"])
