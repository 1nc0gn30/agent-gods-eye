"""Comprehensive test suite for agent-gods-eye.

100% Python Standard Library — Zero External Dependencies.
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
import time
import unittest
import urllib.request
import urllib.error

from agent_gods_eye.shodan_client import ShodanClient
from agent_gods_eye.radar import RadarEngine, TargetNode
from agent_gods_eye.storage import GodsEyeStorage
from agent_gods_eye.server import GodsEyeServer


class TestShodanClient(unittest.TestCase):
    def test_client_init_and_key_detection(self):
        client = ShodanClient(api_key="mock_shodan_key_1234567890")
        self.assertTrue(client.has_valid_key())

    def test_mock_search_results_structure(self):
        client = ShodanClient(api_key=None)
        res = client._mock_search_results("port:554")
        self.assertIn("matches", res)
        self.assertGreater(len(res["matches"]), 0)
        first = res["matches"][0]
        self.assertIn("ip_str", first)
        self.assertIn("port", first)
        self.assertIn("location", first)

    def test_mock_host_details(self):
        client = ShodanClient(api_key=None)
        details = client._mock_host_details("198.51.100.42")
        self.assertEqual(details["ip_str"], "198.51.100.42")
        self.assertIn("ports", details)


class TestRadarEngine(unittest.TestCase):
    def test_lat_lon_to_cartesian(self):
        # Equator at 0, 0
        x, y, z = RadarEngine.lat_lon_to_cartesian(0.0, 0.0, radius=1.0)
        self.assertAlmostEqual(x, 0.0, places=2)
        self.assertAlmostEqual(y, 0.0, places=2)
        self.assertAlmostEqual(z, 1.0, places=2)

        # North Pole at 90, 0
        x_np, y_np, z_np = RadarEngine.lat_lon_to_cartesian(90.0, 0.0, radius=1.0)
        self.assertAlmostEqual(y_np, 1.0, places=2)

    def test_threat_evaluation(self):
        # RTSP camera
        cat, lvl, score = RadarEngine.evaluate_threat(554, "RTSP Server", "H.264 stream", ["CVE-2024-1111"])
        self.assertEqual(cat, "SURVEILLANCE_CAMERA")
        self.assertIn(lvl, ("HIGH", "CRITICAL"))
        self.assertGreaterEqual(score, 50)

        # Modbus SCADA
        cat_scada, lvl_scada, score_scada = RadarEngine.evaluate_threat(502, "Modbus", "Modbus Function Code 3", [])
        self.assertEqual(cat_scada, "SCADA_INDUSTRIAL")
        self.assertGreaterEqual(score_scada, 60)

    def test_normalize_match(self):
        raw = {
            "ip_str": "203.0.113.19",
            "port": 5900,
            "transport": "tcp",
            "org": "Tactical Lab",
            "hostnames": ["vnc.target.com"],
            "product": "VNC",
            "location": {
                "country_code": "DE",
                "country_name": "Germany",
                "city": "Berlin",
                "latitude": 52.5200,
                "longitude": 13.4050
            },
            "vulns": ["CVE-2023-1234"]
        }
        node = RadarEngine.normalize_match(raw)
        self.assertEqual(node.ip, "203.0.113.19")
        self.assertEqual(node.port, 5900)
        self.assertEqual(node.category, "REMOTE_DESKTOP")
        self.assertEqual(node.country, "DE")
        self.assertIsNotNone(node.x)
        self.assertIsNotNone(node.y)
        self.assertIsNotNone(node.z)


class TestGodsEyeStorage(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_godseye.db")
        self.storage = GodsEyeStorage(self.db_path)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_storage_operations(self):
        search_id = self.storage.log_search("port:554", 100, 10)
        self.assertGreater(search_id, 0)

        nodes = [
            {
                "ip": "1.2.3.4",
                "port": 80,
                "org": "Test Corp",
                "hostname": "test.com",
                "country": "US",
                "country_name": "United States",
                "city": "Fairfax",
                "latitude": 38.8462,
                "longitude": -77.3064,
                "category": "WEB_INTERFACE",
                "threat_level": "LOW",
                "threat_score": 25,
                "product": "nginx"
            }
        ]
        upserted = self.storage.upsert_targets(nodes)
        self.assertEqual(upserted, 1)

        targets = self.storage.get_recent_targets(limit=10)
        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0]["ip"], "1.2.3.4")

        stats = self.storage.get_stats()
        self.assertEqual(stats["total_targets"], 1)
        self.assertEqual(stats["total_searches"], 1)


class TestGodsEyeServerIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.db_path = os.path.join(cls.tmp_dir.name, "server_test_godseye.db")
        cls.storage = GodsEyeStorage(cls.db_path)
        cls.shodan = ShodanClient(api_key=None)

        cls.public_dir = os.path.join(cls.tmp_dir.name, "public")
        os.makedirs(cls.public_dir, exist_ok=True)
        with open(os.path.join(cls.public_dir, "index.html"), "w") as f:
            f.write("<html><body>Gods Eye Mock UI</body></html>")

        cls.port = 18112
        cls.server = GodsEyeServer(
            host="127.0.0.1",
            port=cls.port,
            shodan=cls.shodan,
            storage=cls.storage,
            public_dir=cls.public_dir
        )
        cls.t = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.t.start()
        time.sleep(0.3)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.tmp_dir.cleanup()

    def test_health_endpoint(self):
        url = f"http://127.0.0.1:{self.port}/health"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["status"], "ok")
            self.assertEqual(data["service"], "agent-gods-eye")

    def test_search_and_stats(self):
        url = f"http://127.0.0.1:{self.port}/api/search?q=port:554&limit=5"
        with urllib.request.urlopen(url, timeout=3.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("targets", data)
            self.assertGreater(len(data["targets"]), 0)

        # Check stats endpoint
        url_stats = f"http://127.0.0.1:{self.port}/api/stats"
        with urllib.request.urlopen(url_stats, timeout=3.0) as resp:
            self.assertEqual(resp.status, 200)
            s_data = json.loads(resp.read().decode("utf-8"))
            self.assertGreater(s_data["total_targets"], 0)


if __name__ == "__main__":
    unittest.main()
