"""Web Cockpit and Tactical Radar REST API Server.

100% Python Standard Library — Zero External Dependencies.
Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform.
"""

from __future__ import annotations

import csv
import http.server
import io
import json
import mimetypes
import os
import queue
import re
import socketserver
import time
import urllib.parse
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .radar import RadarEngine
from .shodan_client import ShodanClient, VERSION, validate_public_ip
from .storage import GodsEyeStorage

MAX_BODY_BYTES = 1_048_576  # 1 MiB strict cap on POST bodies

_LOCAL_ORIGIN_RE = re.compile(
    r"^https?://(?:127\.0\.0\.1|localhost|\[::1\])(?::(\d{1,5}))?$",
    re.IGNORECASE,
)
_EXPLICIT_ALLOWED_ORIGINS = frozenset({
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "https://zoth.nullai.tech",
})
_LOCAL_HOST_RE = re.compile(
    r"^(?:127\.0\.0\.1|localhost|\[::1\])(?::(\d{1,5}))?$",
    re.IGNORECASE,
)


def _has_traversal(raw: str) -> bool:
    """Detect path traversal attempts across single/double-encoded segments."""
    if not raw:
        return False
    cur = str(raw)
    for _ in range(2):
        if "\x00" in cur or "\\" in cur:
            return True
        parts = [p for p in cur.split("/") if p]
        if any(p == ".." for p in parts):
            return True
        if parts and ":" in parts[0]:
            return True
        cur = urllib.parse.unquote(cur)
    return False


def _safe_rel(raw: str) -> str:
    """Request path -> safe relative path inside a static dir; '' (index) if it
    tries to climb out with '..' or is absolute."""
    if _has_traversal(raw):
        return ""
    rel = urllib.parse.unquote(str(raw or "")).replace("\\", "/").lstrip("/")
    parts = [p for p in rel.split("/") if p not in ("", ".")]
    if any(p == ".." for p in parts) or ":" in (parts[0] if parts else ""):
        return ""
    return "/".join(parts)


def _is_local_origin(origin: Optional[str]) -> bool:
    """Strict Browser Origin check.

    No Origin header = non-browser client (CLI/agent): allowed.
    Otherwise only exact http(s)://127.0.0.1[:port], localhost[:port], [::1][:port]
    (with integer port 1..65535) or explicit Studio origin https://zoth.nullai.tech.
    Rejects port-suffix spoofing such as http://127.0.0.1:8112.example.invalid.
    """
    if not origin:
        return True
    s = str(origin).strip()
    if s in _EXPLICIT_ALLOWED_ORIGINS:
        return True
    m = _LOCAL_ORIGIN_RE.match(s)
    if not m:
        return False
    port_str = m.group(1)
    if port_str is not None:
        port_num = int(port_str)
        if not (1 <= port_num <= 65535):
            return False
    return True


def _is_valid_host(host_header: Optional[str], expected_port: Optional[int] = None) -> bool:
    """Validate HTTP Host header against loopback names to block DNS rebinding."""
    if not host_header:
        return True
    s = str(host_header).strip()
    m = _LOCAL_HOST_RE.match(s)
    if not m:
        return False
    port_str = m.group(1)
    if port_str is not None:
        port_num = int(port_str)
        if not (1 <= port_num <= 65535):
            return False
        if expected_port is not None and port_num != expected_port:
            return False
    return True


def _csv_safe_cell(val: Any) -> str:
    """Neutralize spreadsheet formula injection (=, +, -, @, tab, CR) for CSV cells."""
    s = "" if val is None else str(val)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + s
    return s


def _parse_int_param(raw_val: Any, name: str, default: int, min_val: int, max_val: int) -> Tuple[Optional[int], Optional[str]]:
    """Parse integer query/body parameter, rejecting non-ints or < min_val with 400 and clamping > max_val."""
    if raw_val is None or raw_val == "":
        return default, None
    if isinstance(raw_val, bool):
        return None, f"Invalid '{name}' parameter: must be an integer"
    try:
        v = int(str(raw_val).strip())
    except (ValueError, TypeError):
        return None, f"Invalid '{name}' parameter: must be an integer"
    if v < min_val:
        return None, f"Invalid '{name}' parameter: must be >= {min_val}"
    if v > max_val:
        v = max_val
    return v, None


class GodsEyeHandler(http.server.BaseHTTPRequestHandler):
    """Serves the dual-theme 3D Tactical Radar and Shodan OSINT REST API."""

    server: GodsEyeServer

    def log_message(self, format: str, *args: Any) -> None:
        pass

    def _allowed_origin_header(self) -> Optional[str]:
        origin = self.headers.get("Origin")
        if origin and _is_local_origin(origin):
            return origin.strip()
        return None

    def _guard_request(self, check_origin: bool = True) -> bool:
        """Validate Host and (optionally) Origin headers. Sends 403 and returns False on rejection."""
        if not _is_valid_host(self.headers.get("Host"), getattr(self.server, "server_port", None)):
            self._send_error_json({"error": "invalid host header"}, status=403, emit_cors=False)
            return False

        if check_origin:
            origin = self.headers.get("Origin")
            if origin and not _is_local_origin(origin):
                self._send_error_json({"error": "cross-origin request blocked"}, status=403, emit_cors=False)
                return False
        return True

    def _send_error_json(self, data: Dict[str, Any], status: int = 400, emit_cors: bool = True) -> None:
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Vary", "Origin")
        if emit_cors:
            allowed = self._allowed_origin_header()
            if allowed:
                self.send_header("Access-Control-Allow-Origin", allowed)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, data: Any, status: int = 200) -> None:
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Vary", "Origin")
        allowed = self._allowed_origin_header()
        if allowed:
            self.send_header("Access-Control-Allow-Origin", allowed)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_csv_export(self, targets: list[Dict[str, Any]]) -> None:
        buf = io.StringIO()
        writer = csv.writer(buf, quoting=csv.QUOTE_MINIMAL)
        writer.writerow([
            "ip", "latitude", "longitude", "country_name", "city",
            "org", "threat_score", "ports", "is_simulated",
        ])
        for t in targets:
            raw_ports = t.get("ports")
            if isinstance(raw_ports, list) and raw_ports:
                ports_list = raw_ports
            elif t.get("port"):
                ports_list = [t.get("port")]
            else:
                ports_list = []
            ports_str = ";".join(str(p) for p in ports_list)
            writer.writerow([
                _csv_safe_cell(t.get("ip", "")),
                _csv_safe_cell(t.get("latitude", "")),
                _csv_safe_cell(t.get("longitude", "")),
                _csv_safe_cell(t.get("country_name", "")),
                _csv_safe_cell(t.get("city", "")),
                _csv_safe_cell(t.get("org", "")),
                _csv_safe_cell(t.get("threat_score", "")),
                _csv_safe_cell(ports_str),
                _csv_safe_cell(bool(t.get("is_simulated", False))),
            ])

        body = buf.getvalue().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", 'attachment; filename="godseye_targets.csv"')
        self.send_header("Vary", "Origin")
        allowed = self._allowed_origin_header()
        if allowed:
            self.send_header("Access-Control-Allow-Origin", allowed)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self, allow_empty: bool = False) -> Tuple[Optional[Dict[str, Any]], Optional[Tuple[int, str]]]:
        raw_len = self.headers.get("Content-Length")
        if raw_len is None or raw_len.strip() == "":
            if allow_empty:
                return {}, None
            return None, (400, "JSON object body required")
        try:
            content_len = int(raw_len.strip())
        except ValueError:
            return None, (400, "Invalid Content-Length header")

        if content_len < 0:
            return None, (400, "Invalid Content-Length header")
        if content_len > MAX_BODY_BYTES:
            return None, (413, f"Request body exceeds {MAX_BODY_BYTES} byte limit")
        if content_len == 0:
            if allow_empty:
                return {}, None
            return None, (400, "Empty JSON body")

        raw = self.rfile.read(content_len)
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except Exception:
            return None, (400, "Malformed JSON payload")
        if not isinstance(parsed, dict):
            return None, (400, "JSON payload must be an object")
        return parsed, None

    def _execute_search_request(self, q: str, limit: int, page: int) -> None:
        raw_resp = self.server.shodan.search(q, page=page, limit=limit)
        nodes = RadarEngine.process_search_payload(raw_resp)
        is_sim = bool(raw_resp.get("is_simulated", not raw_resp.get("live", False)))

        self.server.storage.upsert_targets(nodes)
        self.server.storage.log_search(q, raw_resp.get("total", len(nodes)), len(nodes), is_simulated=is_sim)

        self._send_json({
            "query": q,
            "total": raw_resp.get("total", len(nodes)),
            "count": len(nodes),
            "live": bool(raw_resp.get("live", False)),
            "mode": raw_resp.get("mode", "live_shodan" if raw_resp.get("live") else "offline_demo"),
            "is_simulated": is_sim,
            "api_warning": raw_resp.get("api_warning"),
            "targets": nodes,
        })

    def do_OPTIONS(self) -> None:
        if not self._guard_request(check_origin=True):
            return
        self.send_response(204)
        self.send_header("Vary", "Origin")
        allowed = self._allowed_origin_header()
        if allowed:
            self.send_header("Access-Control-Allow-Origin", allowed)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept")
        self.send_header("Access-Control-Max-Age", "600")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        is_api = path == "/health" or path.startswith("/api/")
        if not self._guard_request(check_origin=is_api):
            return

        # 1. Health & /api/health alias
        if path in ("/health", "/api/health"):
            has_key = self.server.shodan.has_valid_key()
            self._send_json({
                "status": "ok",
                "service": "agent-gods-eye",
                "version": VERSION,
                "port": self.server.server_port,
                "has_shodan_key": has_key,
                "mode": "live_shodan" if has_key else "offline_demo",
            })
            return

        # 2. Shodan Account Info
        if path == "/api/info":
            self._send_json(self.server.shodan.get_api_info())
            return

        # 3. Search endpoint
        if path == "/api/search":
            query_params = urllib.parse.parse_qs(parsed.query)
            q = query_params.get("q", ["port:554 has_screenshot:true"])[0]
            limit, err = _parse_int_param(query_params.get("limit", [None])[0], "limit", 30, 1, 500)
            if err or limit is None:
                self._send_error_json({"error": err}, status=400)
                return
            page, err = _parse_int_param(query_params.get("page", [None])[0], "page", 1, 1, 100)
            if err or page is None:
                self._send_error_json({"error": err}, status=400)
                return
            self._execute_search_request(q, limit, page)
            return

        # 4. Host deep inspect (strict IP validation + SSRF/metadata/private rejection)
        if path.startswith("/api/host/"):
            raw_ip = urllib.parse.unquote(path[len("/api/host/"):]).strip()
            canonical_ip, err, code = validate_public_ip(raw_ip)
            if err or not canonical_ip:
                self._send_error_json({"error": err or "Invalid IP"}, status=code)
                return

            details = self.server.shodan.host(canonical_ip)
            stored = self.server.storage.get_targets_by_ip(canonical_ip)
            if stored:
                top = stored[0]
                details.setdefault("ip", canonical_ip)
                details.setdefault("threat_score", top.get("threat_score", 60))
                details.setdefault("threat_level", top.get("threat_level", "HIGH"))
                if not details.get("org") or "Unindexed Host" in str(details.get("org")):
                    details["org"] = top.get("org")
                if not details.get("country_name") or details.get("country_name") == "Offline Demo":
                    details["country_name"] = top.get("country_name")
                if not details.get("city") or details.get("city") == "Not queried upstream":
                    details["city"] = top.get("city")
                if not details.get("latitude"):
                    details["latitude"] = top.get("latitude")
                if not details.get("longitude"):
                    details["longitude"] = top.get("longitude")
                if not details.get("ports"):
                    merged_ports = sorted({p for row in stored for p in (row.get("ports") or [row.get("port")]) if p})
                    details["ports"] = merged_ports
                if not details.get("vulns") and top.get("vulns"):
                    details["vulns"] = top.get("vulns")
                if (not details.get("tags") or details.get("tags") == ["offline-demo"]) and top.get("tags"):
                    details["tags"] = top.get("tags")
                if (not details.get("banner") or "No cached banner" in str(details.get("banner"))) and top.get("banner_snippet"):
                    details["banner"] = top.get("banner_snippet")
            else:
                details.setdefault("ip", details.get("ip_str", canonical_ip))
                ports = details.get("ports") or []
                primary_port = ports[0] if ports else 0
                _cat, lvl, score = RadarEngine.evaluate_threat(
                    primary_port,
                    str(details.get("product") or ""),
                    str(details.get("banner") or ""),
                    details.get("vulns") or [],
                )
                details.setdefault("threat_score", score)
                details.setdefault("threat_level", lvl)

            self._send_json(details)
            return

        # 5. Stats
        if path == "/api/stats":
            stats = self.server.storage.get_stats()
            has_key = self.server.shodan.has_valid_key()
            stats["shodan_connected"] = has_key
            stats["mode"] = "live_shodan" if has_key else "offline_demo"
            stats["version"] = VERSION
            self._send_json(stats)
            return

        # 6. Targets registry
        if path == "/api/targets":
            query_params = urllib.parse.parse_qs(parsed.query)
            limit, err = _parse_int_param(query_params.get("limit", [None])[0], "limit", 50, 1, 500)
            if err or limit is None:
                self._send_error_json({"error": err}, status=400)
                return
            targets = self.server.storage.get_recent_targets(limit=limit)
            self._send_json({"targets": targets, "count": len(targets)})
            return

        # 7. Real JSON Event Log (persisted radar_events)
        if path == "/api/events":
            query_params = urllib.parse.parse_qs(parsed.query)
            limit, err = _parse_int_param(query_params.get("limit", [None])[0], "limit", 50, 1, 500)
            if err or limit is None:
                self._send_error_json({"error": err}, status=400)
                return
            events = self.server.storage.get_recent_events(limit=limit)
            self._send_json({"events": events, "count": len(events)})
            return

        # 8. SSE Live Radar Stream
        if path == "/api/stream":
            self._handle_sse()
            return

        # 9. Export target inventory (JSON / CSV)
        if path == "/api/export":
            query_params = urllib.parse.parse_qs(parsed.query)
            fmt = query_params.get("format", ["json"])[0].lower().strip()
            if fmt not in ("json", "csv"):
                self._send_error_json({"error": "Invalid format: must be 'json' or 'csv'"}, status=400)
                return
            limit, err = _parse_int_param(query_params.get("limit", [None])[0], "limit", 500, 1, 1000)
            if err or limit is None:
                self._send_error_json({"error": err}, status=400)
                return
            targets = self.server.storage.get_recent_targets(limit=limit)
            if fmt == "csv":
                self._send_csv_export(targets)
                return
            self._send_json({
                "export_timestamp": time.time(),
                "version": VERSION,
                "count": len(targets),
                "targets": targets,
            })
            return

        # 10. Unknown /api/* routes return JSON 404 (never SPA HTML fallback)
        if path.startswith("/api/"):
            self._send_error_json({"error": "Endpoint not found", "path": path}, status=404)
            return

        # 11. Static assets
        self._serve_static(path)

    def do_POST(self) -> None:
        if not self._guard_request(check_origin=True):
            return
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/search":
            body, body_err = self._read_json_body(allow_empty=False)
            if body_err:
                self._send_error_json({"error": body_err[1]}, status=body_err[0])
                return
            assert body is not None
            raw_q = body.get("q", body.get("query", "port:554 has_screenshot:true"))
            if not isinstance(raw_q, str):
                self._send_error_json({"error": "Invalid 'q' parameter: must be a string"}, status=400)
                return
            limit, err = _parse_int_param(body.get("limit"), "limit", 30, 1, 500)
            if err or limit is None:
                self._send_error_json({"error": err}, status=400)
                return
            page, err = _parse_int_param(body.get("page"), "page", 1, 1, 100)
            if err or page is None:
                self._send_error_json({"error": err}, status=400)
                return
            self._execute_search_request(raw_q, limit, page)
            return

        if path == "/api/export":
            body, body_err = self._read_json_body(allow_empty=True)
            if body_err:
                self._send_error_json({"error": body_err[1]}, status=body_err[0])
                return
            assert body is not None
            fmt = str(body.get("format", "json")).lower().strip()
            if fmt not in ("json", "csv"):
                self._send_error_json({"error": "Invalid format: must be 'json' or 'csv'"}, status=400)
                return
            limit, err = _parse_int_param(body.get("limit"), "limit", 500, 1, 1000)
            if err or limit is None:
                self._send_error_json({"error": err}, status=400)
                return
            targets = self.server.storage.get_recent_targets(limit=limit)
            if fmt == "csv":
                self._send_csv_export(targets)
                return
            self._send_json({
                "export_timestamp": time.time(),
                "version": VERSION,
                "count": len(targets),
                "targets": targets,
            })
            return

        self._send_error_json({"error": "Endpoint not found", "path": path}, status=404)

    def _handle_sse(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Vary", "Origin")
        allowed = self._allowed_origin_header()
        if allowed:
            self.send_header("Access-Control-Allow-Origin", allowed)
        self.end_headers()

        q = self.server.storage.subscribe_sse()
        stats = self.server.storage.get_stats()
        stats["shodan_connected"] = self.server.shodan.has_valid_key()
        stats["mode"] = "live_shodan" if stats["shodan_connected"] else "offline_demo"
        init_event = f"event: init\ndata: {json.dumps(stats)}\n\n"
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
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            self.server.storage.unsubscribe_sse(q)

    def _serve_static(self, raw_path: str) -> None:
        if _has_traversal(raw_path):
            self._send_error_json({"error": "Forbidden path"}, status=403, emit_cors=False)
            return

        clean_path = _safe_rel(raw_path)
        if not clean_path:
            clean_path = "index.html"

        public_root = Path(self.server.public_dir).resolve()
        candidate = (public_root / clean_path).resolve()

        if not candidate.is_relative_to(public_root):
            self._send_error_json({"error": "Forbidden path"}, status=403, emit_cors=False)
            return

        if not candidate.exists() or candidate.is_dir():
            candidate = (public_root / "index.html").resolve()

        if not candidate.exists() or not candidate.is_relative_to(public_root):
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"404 Not Found")
            return

        content_type, _ = mimetypes.guess_type(str(candidate))
        content_type = content_type or "application/octet-stream"

        try:
            data = candidate.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-cache")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(data)
        except Exception:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Internal server error")


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
        public_dir: str,
    ):
        self.shodan = shodan
        self.storage = storage
        self.public_dir = public_dir
        super().__init__((host, port), GodsEyeHandler)
