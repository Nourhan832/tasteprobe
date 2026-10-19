import json
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from server import Server


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = Server(("127.0.0.1", 0))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = "http://127.0.0.1:"+str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def post(self, path, body, headers=None):
        req = Request(self.base+path, data=json.dumps(body).encode(),
                      headers=headers or {"Content-Type": "application/json"})
        return json.load(urlopen(req, timeout=5))

    def test_browser_contract(self):
        with urlopen(self.base+"/") as response:
            self.assertIn("text/html", response.headers["Content-Type"])
            self.assertIn("frame-ancestors 'none'", response.headers["Content-Security-Policy"])
        state = self.post("/api/session", {"mode": "demo"})
        state = self.post("/api/answer", {"session_id": state["session_id"],
                          "entity_id": state["next"]["entity_id"], "answer": "like"})
        self.assertEqual(state["answered"], 1)

    def test_cross_origin_rejected(self):
        with self.assertRaises(HTTPError) as ctx:
            self.post("/api/session", {}, {"Content-Type": "application/json", "Origin": "https://untrusted.example"})
        self.assertEqual(ctx.exception.code, 403)

    def test_invalid_json_type_and_missing_session(self):
        for body, code in (([], 400), ({"session_id": "missing"}, 410)):
            with self.assertRaises(HTTPError) as ctx:
                self.post("/api/state", body)
            self.assertEqual(ctx.exception.code, code)

    def test_private_source_not_served(self):
        for path in ("/qloo.py", "/.env", "/../service.py"):
            with self.assertRaises(HTTPError) as ctx:
                urlopen(self.base+path)
            self.assertEqual(ctx.exception.code, 404)
