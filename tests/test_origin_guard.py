"""Only local pages (and explicit Studio origin) may call this server from a browser."""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from agent_gods_eye.server import _is_local_origin, _is_valid_host


class TestOriginGuard(unittest.TestCase):
    def test_allowed(self):
        for o in (
            None,
            "",
            "http://127.0.0.1:8000",
            "http://127.0.0.1:8112",
            "http://localhost:3000",
            "http://[::1]:1",
            "https://zoth.nullai.tech",
        ):
            self.assertTrue(_is_local_origin(o), o)

    def test_blocked(self):
        for o in (
            "https://evil.example",
            "null",
            "http://127.0.0.1.evil.com",
            "http://127.0.0.1:8112.example.invalid",
            "http://localhost:3000.evil.example",
            "http://127.0.0.1:99999",
            "http://127.0.0.1:0",
            "file://",
            "chrome-extension://abc",
        ):
            self.assertFalse(_is_local_origin(o), o)

    def test_host_header_guard(self):
        self.assertTrue(_is_valid_host("127.0.0.1:8112", 8112))
        self.assertTrue(_is_valid_host("localhost:8112", 8112))
        self.assertTrue(_is_valid_host("[::1]:8112", 8112))
        self.assertFalse(_is_valid_host("evil.example:8112", 8112))
        self.assertFalse(_is_valid_host("127.0.0.1:8112.evil.com", 8112))


if __name__ == "__main__":
    unittest.main()
