import contextlib
import io
import os
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import start_live


class LauncherTests(unittest.TestCase):
    def test_launch_does_not_depend_on_upstream_availability(self):
        server = Mock()
        output = io.StringIO()
        with patch.dict(os.environ, {}, clear=True), \
             patch("start_live.Path.home", return_value=Path.cwd()), \
             patch("start_live.getpass.getpass", return_value="dummy-private-test-value"), \
             patch("start_live.Server", return_value=server), \
             patch("start_live.watch_and_serve", side_effect=KeyboardInterrupt), \
             patch("qloo.Qloo.search", side_effect=TimeoutError) as search, \
             contextlib.redirect_stdout(output):
            start_live.main()
            search.assert_not_called()
            self.assertNotIn("QLOO_API_KEY", os.environ)
        self.assertIn("http://127.0.0.1:8767", output.getvalue())
        self.assertNotIn("dummy-private-test-value", output.getvalue())
        server.server_close.assert_called_once()

    def test_empty_key_does_not_start_server(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch("start_live.Path.home", return_value=Path.cwd()), \
             patch("start_live.getpass.getpass", return_value=" "), \
             patch("start_live.Server") as server, \
             contextlib.redirect_stdout(io.StringIO()):
            start_live.main()
            server.assert_not_called()
            self.assertNotIn("QLOO_API_KEY", os.environ)
