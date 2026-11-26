"""Comprehensive security, REST API, IP-validation, CSV, SSE, CLI, TUI & MCP test suite.

100% Python Standard Library — Zero External Dependencies.
"""

from __future__ import annotations

import csv
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request

from agent_gods_eye import __version__
from agent_gods_eye.mcp_server import GodsEyeMCPServer
from agent_gods_eye.radar import RadarEngine
from agent_gods_eye.server import GodsEyeServer, _is_local_origin, _is_valid_host
from agent_gods_eye.shodan_client import ShodanClient, validate_public_ip
from agent_gods_eye.storage import GodsEyeStorage

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _http_request(url: str, method: str = "GET", headers: dict | None = None, body: bytes | None = None):
    req = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            return resp.status, dict(resp.headers.items()), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers.items()), e.read()


class TestShodanClientAndIPValidation(unittest.TestCase):
    def test_version_unified(self):
        self.assertEqual(__version__, "2.6.0")

    def test_client_init_and_key_detection(self):
        client = ShodanClient(api_key="mock_shodan_key_1234567890")
        self.assertTrue(client.has_valid_key())
        scrubbed = client._scrub_secret("Error https://api.shodan.io/api-info?key=mock_shodan_key_1234567890")
        self.assertNotIn("mock_shodan_key_1234567890", scrubbed)
        self.assertIn("[REDACTED]", scrubbed)

    def test_ip_validation_blocks_ssrf_and_malformed(self):
        # Malformed -> 400
        for bad in ("not-an-ip", "198.51.100.42/evil", "1.1.1.1?key=abc", "", "999.999.999.999"):
            ip, err, code = validate_public_ip(bad)
            self.assertIsNone(ip, bad)
            self.assertEqual(code, 400, bad)

        # Loopback, private, link-local/metadata, multicast, reserved -> 403
        for blocked in ("127.0.0.1", "::1", "169.254.169.254", "10.0.0.1", "172.16.0.5", "192.168.1.1", "fe80::1", "224.0.0.1", "0.0.0.0"):
            ip, err, code = validate_public_ip(blocked)
            self.assertIsNone(ip, blocked)
            self.assertEqual(code, 403, blocked)

        # RFC 5737 & valid public IPs -> 200
        for ok in ("198.51.100.42", "203.0.113.19", "192.0.2.78", "1.1.1.1"):
            ip, err, code = validate_public_ip(ok)
            self.assertEqual(ip, ok)
            self.assertIsNone(err)
            self.assertEqual(code, 200)

    def test_offline_search_filters_honestly_and_uses_only_rfc5737(self):
        client = ShodanClient(api_key="")
        modbus = client._mock_search_results("port:502 modbus")
        self.assertEqual(modbus["mode"], "offline_demo")
        self.assertTrue(modbus["is_simulated"])
        self.assertGreater(len(modbus["matches"]), 0)
        for m in modbus["matches"]:
            self.assertEqual(m["port"], 502)
            self.assertTrue(
                m["ip_str"].startswith(("192.0.2.", "198.51.100.", "203.0.113.")),
                f"Non-RFC5737 IP leaked: {m['ip_str']}",
            )

        redis = client._mock_search_results("port:6379")
        self.assertEqual(len(redis["matches"]), 1)
        self.assertEqual(redis["matches"][0]["port"], 6379)

    def test_mock_host_details_consistent_with_catalog(self):
        client = ShodanClient(api_key="")
        details = client._mock_host_details("203.0.113.19")
        self.assertEqual(details["ip_str"], "203.0.113.19")
        self.assertIn(502, details["ports"])
        self.assertEqual(details["country_name"], "Germany")
        self.assertTrue(details["is_simulated"])


class TestRadarEngine(unittest.TestCase):
    def test_lat_lon_to_cartesian(self):
        x, y, z = RadarEngine.lat_lon_to_cartesian(0.0, 0.0, radius=1.0)
        self.assertAlmostEqual(x, 0.0, places=2)
        self.assertAlmostEqual(y, 0.0, places=2)
        self.assertAlmostEqual(z, 1.0, places=2)

    def test_threat_evaluation(self):
        cat, lvl, score = RadarEngine.evaluate_threat(554, "RTSP Server", "H.264 stream", ["CVE-2024-1111"])
        self.assertEqual(cat, "SURVEILLANCE_CAMERA")
        self.assertIn(lvl, ("HIGH", "CRITICAL"))
        self.assertGreaterEqual(score, 50)

        cat_scada, _lvl_scada, score_scada = RadarEngine.evaluate_threat(502, "Modbus", "Modbus Function Code 3", [])
        self.assertEqual(cat_scada, "SCADA_INDUSTRIAL")
        self.assertGreaterEqual(score_scada, 60)


class TestGodsEyeStorage(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_godseye.db")
        self.storage = GodsEyeStorage(self.db_path)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_unique_countries_not_capped_at_10_and_events_persisted(self):
        countries = [f"C{i:02d}" for i in range(15)]
        nodes = [
            {
                "ip": f"198.51.100.{i + 1}",
                "port": 80,
                "ports": [80, 443],
                "org": f"=SUM(1,1) Org {i}",
                "hostname": f"host{i}.test.invalid",
                "country": cc,
                "country_name": f"Country {cc}",
                "city": "City",
                "latitude": 10.0,
                "longitude": 20.0,
                "category": "WEB_INTERFACE",
                "threat_level": "LOW",
                "threat_score": 25,
                "product": "nginx",
                "is_simulated": True,
            }
            for i, cc in enumerate(countries)
        ]
        self.storage.upsert_targets(nodes)
        self.storage.log_search("port:80", 15, 15, is_simulated=True)

        stats = self.storage.get_stats()
        self.assertEqual(stats["unique_countries"], 15)
        self.assertEqual(stats["simulated_targets"], 15)

        events = self.storage.get_recent_events(limit=10)
        self.assertGreaterEqual(len(events), 2)


class TestGodsEyeServerIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.db_path = os.path.join(cls.tmp_dir.name, "server_test_godseye.db")
        cls.storage = GodsEyeStorage(cls.db_path)
        cls.shodan = ShodanClient(api_key="")

        cls.public_dir = os.path.join(cls.tmp_dir.name, "public")
        os.makedirs(cls.public_dir, exist_ok=True)
        with open(os.path.join(cls.public_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write("<html><body>Gods Eye Mock UI</body></html>")

        cls.port = 18114
        cls.base = f"http://127.0.0.1:{cls.port}"
        cls.server = GodsEyeServer(
            host="127.0.0.1",
            port=cls.port,
            shodan=cls.shodan,
            storage=cls.storage,
            public_dir=cls.public_dir,
        )
        cls.t = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.t.start()
        time.sleep(0.25)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.tmp_dir.cleanup()

    def test_health_and_api_health_and_zero_acao_on_root(self):
        for ep in ("/health", "/api/health"):
            code, hdrs, raw = _http_request(self.base + ep)
            self.assertEqual(code, 200)
            data = json.loads(raw.decode())
            self.assertEqual(data["version"], "2.6.0")
            self.assertEqual(data["port"], self.port)
            self.assertEqual(data["mode"], "offline_demo")
            self.assertIn("Origin", hdrs.get("Vary", ""))

        # GET / must NOT emit Access-Control-Allow-Origin
        code, hdrs, _raw = _http_request(self.base + "/")
        self.assertEqual(code, 200)
        self.assertNotIn("Access-Control-Allow-Origin", hdrs)

    def test_origin_port_suffix_spoof_host_guard_and_options(self):
        self.assertFalse(_is_local_origin("http://127.0.0.1:8112.example.invalid"))
        self.assertFalse(_is_valid_host("evil.example:18114", self.port))

        # Origin port-suffix spoof -> 403 & zero ACAO on OPTIONS, GET, POST
        spoof = {"Origin": f"http://127.0.0.1:{self.port}.example.invalid"}
        for method, path in (("OPTIONS", "/api/export"), ("GET", "/api/stats"), ("POST", "/api/export")):
            code, hdrs, _ = _http_request(self.base + path, method=method, headers=spoof, body=b"{}" if method == "POST" else None)
            self.assertEqual(code, 403, f"{method} {path}")
            self.assertNotIn("Access-Control-Allow-Origin", hdrs)

        # Allowed Studio origin OPTIONS -> 204 + ACAO + Vary
        code, hdrs, _ = _http_request(self.base + "/api/stats", method="OPTIONS", headers={"Origin": "http://127.0.0.1:3000"})
        self.assertEqual(code, 204)
        self.assertEqual(hdrs.get("Access-Control-Allow-Origin"), "http://127.0.0.1:3000")
        self.assertEqual(hdrs.get("Vary"), "Origin")
        self.assertNotEqual(hdrs.get("Access-Control-Allow-Headers"), "*")

        # Foreign Host header -> 403
        code, _hdrs, _ = _http_request(self.base + "/api/stats", headers={"Host": f"evil.example:{self.port}"})
        self.assertEqual(code, 403)

    def test_traversal_and_unknown_api_and_bad_query_params(self):
        # Traversal -> 403
        for trav in ("/../server.py", "/%2e%2e/server.py", "/..%2fserver.py"):
            code, _hdrs, _ = _http_request(self.base + trav)
            self.assertEqual(code, 403, trav)

        # Unknown /api/* -> JSON 404
        code, hdrs, raw = _http_request(self.base + "/api/does-not-exist")
        self.assertEqual(code, 404)
        self.assertIn("application/json", hdrs.get("Content-Type", ""))
        self.assertIn("error", json.loads(raw.decode()))

        # Invalid limit/page -> 400 (never connection reset!)
        for bad_q in ("/api/search?limit=abc", "/api/search?page=abc", "/api/targets?limit=abc", "/api/targets?limit=-5"):
            code, _hdrs, _ = _http_request(self.base + bad_q)
            self.assertEqual(code, 400, bad_q)

    def test_host_ip_ssrf_and_consistent_inspect(self):
        code, _, _ = _http_request(self.base + "/api/host/not-an-ip")
        self.assertEqual(code, 400)
        for blocked in ("127.0.0.1", "169.254.169.254", "10.0.0.1", "192.168.1.1"):
            code, _, _ = _http_request(self.base + f"/api/host/{blocked}")
            self.assertEqual(code, 403, blocked)

        code, _, raw = _http_request(self.base + "/api/host/203.0.113.19")
        self.assertEqual(code, 200)
        data = json.loads(raw.decode())
        self.assertIn(502, data["ports"])
        self.assertEqual(data["country_name"], "Germany")

    def test_post_search_validation_body_cap_events_and_csv_export(self):
        # Valid POST /api/search
        code, _, raw = _http_request(
            self.base + "/api/search",
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps({"q": "port:502 modbus", "limit": 5}).encode(),
        )
        self.assertEqual(code, 200)
        data = json.loads(raw.decode())
        self.assertGreater(data["count"], 0)
        self.assertTrue(all(t["port"] == 502 for t in data["targets"]))

        # Malformed & non-dict JSON -> 400
        for bad_body in (b"{not-json", b'["array"]'):
            code, _, _ = _http_request(self.base + "/api/search", method="POST", body=bad_body)
            self.assertEqual(code, 400)

        # Oversized body (> 1 MiB) -> 413
        code, _, _ = _http_request(self.base + "/api/search", method="POST", body=b"a" * (1_048_576 + 10))
        self.assertEqual(code, 413)

        # JSON /api/events populated
        code, hdrs, raw = _http_request(self.base + "/api/events")
        self.assertEqual(code, 200)
        self.assertIn("application/json", hdrs.get("Content-Type", ""))
        ev_data = json.loads(raw.decode())
        self.assertGreater(ev_data["count"], 0)

        # Inject formula-bearing org row and verify CSV ports + formula neutralization + CORS/Vary
        self.storage.upsert_targets([{
            "ip": "192.0.2.99",
            "port": 6379,
            "ports": [6379],
            "org": "=CMD|' /C calc'!A0",
            "hostname": "redis.test.invalid",
            "country": "US",
            "country_name": "United States",
            "city": "Test",
            "latitude": 1.0,
            "longitude": 2.0,
            "category": "DATABASE_CLUSTER",
            "threat_level": "HIGH",
            "threat_score": 70,
            "product": "Redis",
            "is_simulated": True,
        }])
        code, hdrs, raw = _http_request(
            self.base + "/api/export?format=csv",
            headers={"Origin": "http://127.0.0.1:3000"},
        )
        self.assertEqual(code, 200)
        self.assertEqual(hdrs.get("Access-Control-Allow-Origin"), "http://127.0.0.1:3000")
        self.assertEqual(hdrs.get("Vary"), "Origin")
        rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8"))))
        self.assertTrue(any(r["ip"] == "192.0.2.99" and r["ports"] == "6379" and r["org"].startswith("'=CMD") for r in rows))


class TestCLITUIAndMCP(unittest.TestCase):
    def test_cli_search_json_and_tui_once(self):
        env = {k: v for k, v in os.environ.items() if k not in ("SHODAN_API_KEY", "SHODAN_API")}
        env["HOME"] = tempfile.mkdtemp(prefix="age-test-home-")
        env["PYTHONPATH"] = os.path.join(REPO_ROOT, "src")

        res = subprocess.run(
            [sys.executable, os.path.join(REPO_ROOT, "bin", "agent-gods-eye"), "search", "port:502 modbus", "--limit", "5", "--json"],
            capture_output=True, text=True, env=env, check=True,
        )
        payload = json.loads(res.stdout)
        self.assertEqual(payload["version"], "2.6.0")
        self.assertEqual(payload["mode"], "offline_demo")
        self.assertTrue(all(t["port"] == 502 for t in payload["targets"]))

        tui = subprocess.run(
            [sys.executable, os.path.join(REPO_ROOT, "bin", "agent-gods-eye-tui"), "--json", "--port", "19999"],
            capture_output=True, text=True, env=env, check=True,
        )
        tui_data = json.loads(tui.stdout)
        self.assertEqual(tui_data["tool"], "agent-gods-eye")
        self.assertEqual(tui_data["version"], "2.6.0")
        self.assertNotIn("canvasui-html-effects", tui.stdout)

    def test_mcp_stdio_tools(self):
        with tempfile.TemporaryDirectory() as tmp:
            mcp = GodsEyeMCPServer(db_path=os.path.join(tmp, "mcp.db"), api_key="")
            init = mcp.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
            self.assertEqual(init["result"]["serverInfo"]["version"], "2.6.0")

            listed = mcp.handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
            names = [t["name"] for t in listed["result"]["tools"]]
            self.assertEqual(names, ["agent_gods_eye_execute", "gods_eye_search", "gods_eye_host", "gods_eye_stats"])

            # Call agent_gods_eye_execute search
            called = mcp.handle_request({
                "jsonrpc": "2.0", "id": 3, "method": "tools/call",
                "params": {"name": "agent_gods_eye_execute", "arguments": {"action": "search", "target": "port:502 modbus", "limit": 5}},
            })
            self.assertFalse(called["result"]["isError"])
            body = json.loads(called["result"]["content"][0]["text"])
            self.assertEqual(body["status"], "SUCCESS")
            self.assertGreater(body["results"]["count"], 0)

            # Call gods_eye_host with blocked metadata IP
            blocked = mcp.handle_request({
                "jsonrpc": "2.0", "id": 4, "method": "tools/call",
                "params": {"name": "gods_eye_host", "arguments": {"ip": "169.254.169.254"}},
            })
            self.assertTrue(blocked["result"]["isError"])


if __name__ == "__main__":
    unittest.main()
