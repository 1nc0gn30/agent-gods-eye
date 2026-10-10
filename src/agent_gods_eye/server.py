"""Web Cockpit and Tactical Radar REST API Server.

100% Python Standard Library — Zero External Dependencies.
"""

from __future__ import annotations

import http.server
import json
import mimetypes
import os
import queue
import socketserver
import time
import urllib.parse
from typing import Any, Dict, Optional

from .radar import RadarEngine
from .shodan_client import ShodanClient
from .storage import GodsEyeStorage


class GodsEyeHandler(http.server.BaseHTTPRequestHandler):
    """Serves the avant-garde 3D Tactical Radar and Shodan OSINT endpoints."""

    server: GodsEyeServer

    def log_message(self, format: str, *args: Any) -> None:
        pass

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # 1. Health
        if path == "/health":
            self._send_json({
                "status": "ok",
                "service": "agent-gods-eye",
                "version": "1.0.0",
                "port": self.server.server_port,
                "has_shodan_key": self.server.shodan.has_valid_key()
            })
            return

        # 2. Shodan Account Info
        if path == "/api/info":
            info = self.server.shodan.get_api_info()
            self._send_json(info)
            return

        # 3. Search endpoint
        if path == "/api/search":
            query_params = urllib.parse.parse_qs(parsed.query)
            q = query_params.get("q", ["has_screenshot:true"])[0]
            limit = int(query_params.get("limit", [30])[0])
            page = int(query_params.get("page", [1])[0])

            raw_resp = self.server.shodan.search(q, page=page, limit=limit)
            nodes = RadarEngine.process_search_payload(raw_resp)
            
            # Persist in storage
            self.server.storage.upsert_targets(nodes)
            self.server.storage.log_search(q, raw_resp.get("total", len(nodes)), len(nodes))

            self._send_json({
                "query": q,
                "total": raw_resp.get("total", len(nodes)),
                "count": len(nodes),
                "live": raw_resp.get("live", False),
                "api_warning": raw_resp.get("api_warning"),
                "targets": nodes
            })
            return

        # 4. Host deep inspect
        if path.startswith("/api/host/"):
            ip = path.split("/api/host/")[1].strip()
            details = self.server.shodan.host(ip)
            self._send_json(details)
            return

        # 5. Stats
        if path == "/api/stats":
            stats = self.server.storage.get_stats()
            stats["shodan_connected"] = self.server.shodan.has_valid_key()
            self._send_json(stats)
            return

        # 6. Targets registry
        if path == "/api/targets":
            query_params = urllib.parse.parse_qs(parsed.query)
            limit = int(query_params.get("limit", [50])[0])
            targets = self.server.storage.get_recent_targets(limit=limit)
            self._send_json({"targets": targets, "count": len(targets)})
            return

        # 7. SSE Live Radar Stream
        if path in ("/api/stream", "/api/events"):
            self._handle_sse()
            return

        # 8. Export target inventory
        if path == "/api/export":
            query_params = urllib.parse.parse_qs(parsed.query)
            fmt = query_params.get("format", ["json"])[0]
            targets = self.server.storage.get_recent_targets(limit=1000)
            if fmt == "csv":
                csv_lines = ["ip,latitude,longitude,country_name,city,org,threat_score,ports"]
                for t in targets:
                    ports_str = ";".join(str(p) for p in t.get("ports", []))
                    csv_lines.append(f'"{t.get("ip")}","{t.get("latitude")}","{t.get("longitude")}","{t.get("country_name")}","{t.get("city")}","{t.get("org")}","{t.get("threat_score")}","{ports_str}"')
                body = "\n".join(csv_lines).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/csv")
                self.send_header("Content-Disposition", 'attachment; filename="godseye_targets.csv"')
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            self._send_json({"export_timestamp": time.time(), "count": len(targets), "targets": targets})
            return

        # 9. Static assets
        self._serve_static(path)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/export":
            # Return current target database as JSON bundle
            targets = self.server.storage.get_recent_targets(limit=500)
            self._send_json({"export_timestamp": time.time(), "targets": targets})
            return

        self._send_json({"error": "Endpoint not found"}, status=404)

    def _handle_sse(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        q = self.server.storage.subscribe_sse()
        init_event = f"event: init\ndata: {json.dumps(self.server.storage.get_stats())}\n\n"
        try:
            self.wfile.write(init_event.encode("utf-8"))
            self.wfile.flush()
            while True:
                try:
                    msg = q.get(timeout=10.0)
                    self.wfile.write(msg.encode("utf-8"))
                    self.wfile.flush()
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            self.server.storage.unsubscribe_sse(q)

    def _serve_static(self, path: str) -> None:
        clean_path = path.lstrip("/")
        if not clean_path or clean_path == "":
            clean_path = "index.html"

        file_path = os.path.join(self.server.public_dir, clean_path)
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            file_path = os.path.join(self.server.public_dir, "index.html")

        if not os.path.exists(file_path):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")
            return

        content_type, _ = mimetypes.guess_type(file_path)
        content_type = content_type or "application/octet-stream"

        try:
            with open(file_path, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))

    def _send_json(self, data: Any, status: int = 200) -> None:
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class GodsEyeServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """Threaded HTTP server for Gods Eye tactical radar."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        host: str,
        port: int,
        shodan: ShodanClient,
        storage: GodsEyeStorage,
        public_dir: str
    ):
        self.shodan = shodan
        self.storage = storage
        self.public_dir = public_dir
        super().__init__((host, port), GodsEyeHandler)
