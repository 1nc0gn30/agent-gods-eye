"""Zero-dependency JSON-RPC 2.0 Stdio MCP Server for Agent God's Eye.

100% Python Standard Library — Zero External Dependencies.
Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, List, Optional, TextIO

from .radar import RadarEngine
from .shodan_client import ShodanClient, VERSION, validate_public_ip
from .storage import GodsEyeStorage

MCP_PROTOCOL_VERSION = "2024-11-05"

TOOLS_SPEC: List[Dict[str, Any]] = [
    {
        "name": "agent_gods_eye_execute",
        "description": "Unified dispatcher for Agent God's Eye operations (status, search, host, stats, export).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["status", "search", "host", "stats", "export"],
                    "description": "Operation to execute on Agent God's Eye.",
                },
                "target": {
                    "type": "string",
                    "description": "Search query string (for action='search') or target IP (for action='host').",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results to return (1..500, default 20).",
                },
            },
            "required": ["action"],
        },
    },
    {
        "name": "gods_eye_search",
        "description": "Execute a Shodan OSINT query (or honest RFC 5737 offline demo query when SHODAN_API_KEY is unset) and score discovered targets.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Shodan filter query (e.g. 'port:502 modbus')."},
                "limit": {"type": "integer", "description": "Max hosts to return (1..500, default 20)."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "gods_eye_host",
        "description": "Inspect open ports, geolocation, banners, and CVEs for a validated public or RFC 5737 IP address (blocks loopback/private/metadata IPs).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ip": {"type": "string", "description": "Target IPv4 or IPv6 address."},
            },
            "required": ["ip"],
        },
    },
    {
        "name": "gods_eye_stats",
        "description": "Retrieve aggregated target telemetry, threat breakdown, unique countries, and Shodan live/offline mode status.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]


class GodsEyeMCPServer:
    """Stdio JSON-RPC 2.0 MCP server backed by ShodanClient + GodsEyeStorage."""

    def __init__(self, db_path: str = "godseye.db", api_key: Optional[str] = None):
        self.shodan = ShodanClient(api_key=api_key)
        self.storage = GodsEyeStorage(db_path)

    def _op_stats(self) -> Dict[str, Any]:
        stats = self.storage.get_stats()
        has_key = self.shodan.has_valid_key()
        return {
            "tool": "agent-gods-eye",
            "version": VERSION,
            "port": 8112,
            "mode": "live_shodan" if has_key else "offline_demo",
            "shodan_connected": has_key,
            "stats": stats,
        }

    def _op_search(self, query: str, limit: int = 20) -> Dict[str, Any]:
        lim = max(1, min(500, int(limit or 20)))
        raw = self.shodan.search(query, page=1, limit=lim)
        nodes = RadarEngine.process_search_payload(raw)
        is_sim = bool(raw.get("is_simulated", not raw.get("live", False)))
        self.storage.upsert_targets(nodes)
        self.storage.log_search(query, raw.get("total", len(nodes)), len(nodes), is_simulated=is_sim)
        return {
            "query": query,
            "total": raw.get("total", len(nodes)),
            "count": len(nodes),
            "live": bool(raw.get("live", False)),
            "mode": raw.get("mode", "offline_demo"),
            "is_simulated": is_sim,
            "targets": nodes,
        }

    def _op_host(self, ip: str) -> Dict[str, Any]:
        canonical_ip, err, code = validate_public_ip(ip)
        if err or not canonical_ip:
            return {"error": err or "Invalid IP", "status_code": code}
        return self.shodan.host(canonical_ip)

    def _call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if name == "gods_eye_stats":
            return self._op_stats()

        if name == "gods_eye_search":
            q = str(arguments.get("query") or "port:554 has_screenshot:true")
            lim = int(arguments.get("limit") or 20)
            return self._op_search(q, lim)

        if name == "gods_eye_host":
            ip = str(arguments.get("ip") or "")
            return self._op_host(ip)

        if name == "agent_gods_eye_execute":
            action = str(arguments.get("action") or "status").lower().strip()
            target = str(arguments.get("target") or "").strip()
            lim = int(arguments.get("limit") or 20)
            if action in ("status", "stats"):
                return {"status": "ONLINE", "tool": "agent-gods-eye", "port": 8112, "results": self._op_stats()}
            if action == "search":
                q = target or "port:554 has_screenshot:true"
                return {"status": "SUCCESS", "tool": "agent-gods-eye", "port": 8112, "results": self._op_search(q, lim)}
            if action == "host":
                return {"status": "SUCCESS", "tool": "agent-gods-eye", "port": 8112, "results": self._op_host(target)}
            if action == "export":
                targets = self.storage.get_recent_targets(limit=max(1, min(500, lim)))
                return {"status": "SUCCESS", "tool": "agent-gods-eye", "port": 8112, "results": {"count": len(targets), "targets": targets}}
            return {"error": f"Unsupported action: {action}"}

        raise KeyError(f"Unknown tool: {name}")

    def handle_request(self, req: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params") or {}

        # Notifications without id receive no response
        if method == "notifications/initialized":
            return None

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "agent-gods-eye",
                        "version": VERSION,
                    },
                },
            }

        if method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}

        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS_SPEC}}

        if method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments") or {}
            if not isinstance(tool_args, dict):
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32602, "message": "Tool arguments must be an object"},
                }
            try:
                result = self._call_tool(str(tool_name), tool_args)
                is_err = isinstance(result, dict) and "error" in result
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
                        "isError": is_err,
                    },
                }
            except KeyError as e:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": str(e)},
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32603, "message": f"Tool execution error: {type(e).__name__}"},
                }

        if req_id is None:
            return None

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }

    def serve_stdio(self, stdin: Optional[TextIO] = None, stdout: Optional[TextIO] = None) -> None:
        """Serve newline-delimited JSON-RPC 2.0 requests on stdio."""
        inp = stdin or sys.stdin
        out = stdout or sys.stdout

        for line in inp:
            stripped = line.strip()
            if not stripped:
                continue
            # Support Content-Length header lines gracefully if framed
            if stripped.lower().startswith("content-length:"):
                continue
            try:
                req = json.loads(stripped)
            except json.JSONDecodeError:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": "Parse error"},
                }
                out.write(json.dumps(err_resp) + "\n")
                out.flush()
                continue

            if isinstance(req, dict):
                resp = self.handle_request(req)
                if resp is not None:
                    out.write(json.dumps(resp) + "\n")
                    out.flush()
