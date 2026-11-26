"""Shodan API client using pure Python standard library.

100% Python Standard Library — Zero External Dependencies.
Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform.
"""

from __future__ import annotations

import ipaddress
import json
import logging
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("agent_gods_eye.shodan")

VERSION = "2.6.0"
USER_AGENT = f"AgentGodsEye/{VERSION} (Neal Frazier Tech @1nc0gn30; NullAI Platform)"

# RFC 5737 documentation / demonstration test IPv4 blocks (never routed publicly)
RFC5737_NETWORKS = (
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
)

# Explicitly restricted networks (SSRF / internal / cloud metadata / non-routable)
RESTRICTED_V4_NETWORKS = (
    ipaddress.ip_network("0.0.0.0/8"),        # Unspecified / current network
    ipaddress.ip_network("10.0.0.0/8"),       # RFC 1918 private
    ipaddress.ip_network("100.64.0.0/10"),    # RFC 6598 CGNAT
    ipaddress.ip_network("127.0.0.0/8"),      # Loopback
    ipaddress.ip_network("169.254.0.0/16"),   # Link-local & AWS/GCP/Azure metadata
    ipaddress.ip_network("172.16.0.0/12"),    # RFC 1918 private
    ipaddress.ip_network("192.168.0.0/16"),   # RFC 1918 private
    ipaddress.ip_network("198.18.0.0/15"),    # Benchmarking
    ipaddress.ip_network("224.0.0.0/4"),      # Multicast
    ipaddress.ip_network("240.0.0.0/4"),      # Reserved / broadcast
)


def is_rfc5737_ip(addr: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Return True if address belongs to RFC 5737 documentation ranges."""
    return isinstance(addr, ipaddress.IPv4Address) and any(addr in net for net in RFC5737_NETWORKS)


def validate_public_ip(raw_ip: str) -> Tuple[Optional[str], Optional[str], int]:
    """Strictly validate a target IP address and block SSRF/private/metadata ranges.

    Returns (canonical_ip, error_message, http_status).
    Allows valid public routable IPs and RFC 5737 documentation IPs (for offline demo).
    Rejects malformed strings (400) and loopback/private/link-local/metadata/multicast/reserved (403).
    """
    candidate = (raw_ip or "").strip()
    if not candidate or len(candidate) > 64 or any(c in candidate for c in ("/", "?", "#", "@", " ", "\n", "\r")):
        return None, "Invalid IP address format", 400

    try:
        addr = ipaddress.ip_address(candidate)
    except ValueError:
        return None, "Invalid IP address format", 400

    # Allow RFC 5737 documentation IPs strictly for offline demo catalog (never forwarded upstream)
    if is_rfc5737_ip(addr):
        return str(addr), None, 200

    if isinstance(addr, ipaddress.IPv4Address):
        if any(addr in net for net in RESTRICTED_V4_NETWORKS):
            return None, "Target IP is in a restricted range (loopback, private, link-local/metadata, multicast, or reserved)", 403
        if addr.is_loopback or addr.is_private or addr.is_link_local or addr.is_multicast or addr.is_reserved or addr.is_unspecified:
            return None, "Target IP is not a publicly routable address", 403
    else:
        # Handle IPv4-mapped IPv6 addresses (e.g., ::ffff:127.0.0.1)
        if addr.ipv4_mapped is not None:
            return validate_public_ip(str(addr.ipv4_mapped))
        if addr.is_loopback or addr.is_private or addr.is_link_local or addr.is_multicast or addr.is_reserved or addr.is_unspecified or addr.is_site_local:
            return None, "Target IPv6 address is in a restricted range", 403

    return str(addr), None, 200


# Deterministic RFC 5737 Offline Demo Catalog (ZERO real third-party IPs)
OFFLINE_DEMO_CATALOG: List[Dict[str, Any]] = [
    {
        "ip_str": "198.51.100.42",
        "port": 554,
        "ports": [554, 80, 8000],
        "transport": "tcp",
        "org": "Perimeter Vision Lab (RFC 5737 Demo)",
        "hostnames": ["cam-gate01.test.invalid"],
        "product": "RTSP Stream Server",
        "version": "2.4.1",
        "has_screenshot": True,
        "data": "RTSP/1.0 200 OK\r\nServer: H.264 IPCam Streamer\r\nCSeq: 1\r\nPublic: DESCRIBE, SETUP, TEARDOWN, PLAY\r\n",
        "location": {
            "country_code": "US",
            "country_name": "United States",
            "region_code": "VA",
            "city": "Ashburn",
            "latitude": 39.0438,
            "longitude": -77.4874,
        },
        "vulns": ["CVE-2021-36260"],
        "tags": ["camera", "rtsp", "surveillance", "screenshot"],
        "is_simulated": True,
    },
    {
        "ip_str": "198.51.100.77",
        "port": 554,
        "ports": [554, 37777],
        "transport": "tcp",
        "org": "Harbor Optics Testbed (RFC 5737 Demo)",
        "hostnames": ["dvr-harbor02.test.invalid"],
        "product": "Dahua RTSP Gateway",
        "version": "3.1.0",
        "has_screenshot": True,
        "data": "RTSP/1.0 200 OK\r\nServer: Dahua-RTSP-Gateway\r\nChannels: 1-8\r\n",
        "location": {
            "country_code": "SG",
            "country_name": "Singapore",
            "region_code": "01",
            "city": "Singapore",
            "latitude": 1.3521,
            "longitude": 103.8198,
        },
        "vulns": ["CVE-2021-33044"],
        "tags": ["camera", "rtsp", "dahua", "screenshot"],
        "is_simulated": True,
    },
    {
        "ip_str": "203.0.113.19",
        "port": 502,
        "ports": [502, 102],
        "transport": "tcp",
        "org": "GridSim Substation Lab (RFC 5737 Demo)",
        "hostnames": ["scada-substation04.test.invalid"],
        "product": "Modbus TCP Gateway",
        "version": "1.2",
        "has_screenshot": False,
        "data": "Modbus Unit ID: 1, Function Code: 0x03 (Read Holding Registers), PLC Modicon M340",
        "location": {
            "country_code": "DE",
            "country_name": "Germany",
            "region_code": "BY",
            "city": "Nuremberg",
            "latitude": 49.4521,
            "longitude": 11.0767,
        },
        "vulns": ["CVE-2022-45788"],
        "tags": ["scada", "modbus", "ics", "industrial"],
        "is_simulated": True,
    },
    {
        "ip_str": "203.0.113.55",
        "port": 502,
        "ports": [102, 502, 44818],
        "transport": "tcp",
        "org": "Nordic Turbine Control Sim (RFC 5737 Demo)",
        "hostnames": ["plc-s7-plant02.test.invalid"],
        "product": "Siemens S7 / Modbus PLC",
        "version": "4.5.0",
        "has_screenshot": False,
        "data": "Siemens S7-1200 CPU 1214C Modbus TCP Slave Active",
        "location": {
            "country_code": "GB",
            "country_name": "United Kingdom",
            "region_code": "ENG",
            "city": "London",
            "latitude": 51.5074,
            "longitude": -0.1278,
        },
        "vulns": ["CVE-2019-13945"],
        "tags": ["scada", "modbus", "siemens", "ics"],
        "is_simulated": True,
    },
    {
        "ip_str": "192.0.2.78",
        "port": 27017,
        "ports": [27017],
        "transport": "tcp",
        "org": "Kanto Document Store Lab (RFC 5737 Demo)",
        "hostnames": ["mongo-replica01.test.invalid"],
        "product": "MongoDB Server",
        "version": "6.0.4",
        "has_screenshot": False,
        "data": "MongoDB Server Information: version 6.0.4 authMechanism: NONE",
        "location": {
            "country_code": "JP",
            "country_name": "Japan",
            "region_code": "13",
            "city": "Tokyo",
            "latitude": 35.6895,
            "longitude": 139.6917,
        },
        "vulns": ["CVE-2019-2386"],
        "tags": ["database", "mongodb", "unauthenticated"],
        "is_simulated": True,
    },
    {
        "ip_str": "192.0.2.63",
        "port": 6379,
        "ports": [6379],
        "transport": "tcp",
        "org": "Osaka Cache Cluster Lab (RFC 5737 Demo)",
        "hostnames": ["redis-cache01.test.invalid"],
        "product": "Redis Key-Value Store",
        "version": "7.0.12",
        "has_screenshot": False,
        "data": "+PONG\r\n-NOAUTH Authentication required.\r\nrole:master",
        "location": {
            "country_code": "JP",
            "country_name": "Japan",
            "region_code": "27",
            "city": "Osaka",
            "latitude": 34.6937,
            "longitude": 135.5023,
        },
        "vulns": ["CVE-2022-0543"],
        "tags": ["database", "redis", "cache"],
        "is_simulated": True,
    },
    {
        "ip_str": "198.51.100.101",
        "port": 5900,
        "ports": [5900],
        "transport": "tcp",
        "org": "Seine Remote Lab (RFC 5737 Demo)",
        "hostnames": ["vnc-desktop-paris.test.invalid"],
        "product": "RFB / VNC Remote Display",
        "version": "003.008",
        "has_screenshot": True,
        "data": "RFB 003.008\nSecurity types: None (1) authentication disabled",
        "location": {
            "country_code": "FR",
            "country_name": "France",
            "region_code": "IDF",
            "city": "Paris",
            "latitude": 48.8566,
            "longitude": 2.3522,
        },
        "vulns": ["CVE-2023-38606"],
        "tags": ["vnc", "remote-desktop", "screenshot", "unauthenticated"],
        "is_simulated": True,
    },
    {
        "ip_str": "203.0.113.88",
        "port": 9200,
        "ports": [9200, 9300],
        "transport": "tcp",
        "org": "Southern Cross Telemetry Lab (RFC 5737 Demo)",
        "hostnames": ["es-telemetry-syd.test.invalid"],
        "product": "Elasticsearch Cluster",
        "version": "8.11.0",
        "has_screenshot": False,
        "data": '{"name": "node-syd-01", "cluster_name": "telemetry-demo", "version": {"number": "8.11.0"}}',
        "location": {
            "country_code": "AU",
            "country_name": "Australia",
            "region_code": "NSW",
            "city": "Sydney",
            "latitude": -33.8688,
            "longitude": 151.2093,
        },
        "vulns": [],
        "tags": ["database", "elasticsearch", "telemetry"],
        "is_simulated": True,
    },
    {
        "ip_str": "192.0.2.120",
        "port": 8080,
        "ports": [8080, 8009],
        "transport": "tcp",
        "org": "Paulista Gateway Sim (RFC 5737 Demo)",
        "hostnames": ["iot-gateway-sp.test.invalid"],
        "product": "Apache Tomcat / AJP",
        "version": "9.0.58",
        "has_screenshot": True,
        "data": "HTTP/1.1 200 OK\r\nServer: Apache-Coyote/1.1\r\n",
        "location": {
            "country_code": "BR",
            "country_name": "Brazil",
            "region_code": "SP",
            "city": "Sao Paulo",
            "latitude": -23.5505,
            "longitude": -46.6333,
        },
        "vulns": ["CVE-2020-1938"],
        "tags": ["web", "tomcat", "screenshot"],
        "is_simulated": True,
    },
    {
        "ip_str": "198.51.100.144",
        "port": 11434,
        "ports": [11434, 8000],
        "transport": "tcp",
        "org": "Mumbai Inference Testbed (RFC 5737 Demo)",
        "hostnames": ["ollama-node-bom.test.invalid"],
        "product": "Ollama LLM Inference API",
        "version": "0.1.34",
        "has_screenshot": False,
        "data": "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nOllama is running",
        "location": {
            "country_code": "IN",
            "country_name": "India",
            "region_code": "MH",
            "city": "Mumbai",
            "latitude": 19.0760,
            "longitude": 72.8777,
        },
        "vulns": ["CVE-2024-37032"],
        "tags": ["ai", "llm", "ollama"],
        "is_simulated": True,
    },
]


class ShodanClient:
    """Zero-dependency client for Shodan REST API with honest RFC 5737 offline demo mode."""

    BASE_URL = "https://api.shodan.io"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key if api_key is not None else self._discover_api_key()

    def _discover_api_key(self) -> Optional[str]:
        """Locate Shodan API key from env or ~/.config/shodan/.env."""
        key = os.environ.get("SHODAN_API_KEY") or os.environ.get("SHODAN_API")
        if key:
            return key.strip().strip('"').strip("'")

        env_path = os.path.expanduser("~/.config/shodan/.env")
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("SHODAN_API_KEY=") or line.startswith("SHODAN_API="):
                            val = line.split("=", 1)[1].strip().strip('"').strip("'")
                            if val:
                                return val
            except Exception as e:
                logger.debug("Failed to read Shodan env config: %s", type(e).__name__)

        return None

    def _scrub_secret(self, text: str) -> str:
        """Remove any API key occurrences from error strings or logs."""
        out = str(text or "")
        if self.api_key:
            out = out.replace(self.api_key, "[REDACTED]")
        out = re.sub(r"([?&]key=)[^&\s\"']+", r"\1[REDACTED]", out, flags=re.IGNORECASE)
        return out

    def has_valid_key(self) -> bool:
        """Check if an API key is available."""
        return bool(self.api_key and len(self.api_key) >= 16)

    def get_api_info(self) -> Dict[str, Any]:
        """Retrieve account usage, plan, and remaining query credits."""
        if not self.has_valid_key():
            return {
                "api_configured": False,
                "mode": "offline_demo",
                "plan": "offline",
                "unlocked": False,
                "scan_credits": 0,
                "query_credits": 0,
                "monitored_ips": 0,
                "status": "offline_demo",
                "version": VERSION,
            }

        url = f"{self.BASE_URL}/api-info?{urllib.parse.urlencode({'key': self.api_key})}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                data["api_configured"] = True
                data["mode"] = "live_shodan"
                data["status"] = "connected"
                data["version"] = VERSION
                return data
        except Exception as e:
            return {
                "api_configured": True,
                "mode": "live_shodan",
                "plan": "offline",
                "unlocked": False,
                "scan_credits": 0,
                "query_credits": 0,
                "monitored_ips": 0,
                "error": self._scrub_secret(str(e)),
                "status": "error_or_offline",
                "version": VERSION,
            }

    def search(self, query: str, page: int = 1, limit: int = 30) -> Dict[str, Any]:
        """Search Shodan host database or filter RFC 5737 offline catalog."""
        if not self.has_valid_key():
            return self._mock_search_results(query, page, limit)

        params = urllib.parse.urlencode({
            "key": self.api_key,
            "query": query,
            "page": page,
        })
        url = f"{self.BASE_URL}/shodan/host/search?{params}"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=15.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if "matches" in data and len(data["matches"]) > limit:
                    data["matches"] = data["matches"][:limit]
                data["live"] = True
                data["mode"] = "live_shodan"
                data["is_simulated"] = False
                data["query"] = query
                return data
        except urllib.error.HTTPError as e:
            err_body = self._scrub_secret(e.read().decode("utf-8", errors="replace")[:240])
            logger.warning("Shodan API HTTP Error %s: %s", e.code, err_body)
            res = self._mock_search_results(query, page, limit)
            res["api_warning"] = f"Shodan API ({e.code}): {err_body}. Displaying RFC 5737 offline demo catalog."
            return res
        except Exception as e:
            err_msg = self._scrub_secret(str(e))
            logger.warning("Shodan API connection failed: %s", err_msg)
            res = self._mock_search_results(query, page, limit)
            res["api_warning"] = f"Upstream unreachable ({err_msg}). Operating in RFC 5737 offline demo mode."
            return res

    def host(self, ip: str) -> Dict[str, Any]:
        """Fetch full details for an individual validated IP."""
        canonical_ip, err, _status = validate_public_ip(ip)
        if err or not canonical_ip:
            raise ValueError(err or "Invalid IP")

        addr = ipaddress.ip_address(canonical_ip)
        # Never forward RFC 5737 documentation IPs to live Shodan API
        if not self.has_valid_key() or is_rfc5737_ip(addr):
            return self._mock_host_details(canonical_ip)

        url = f"{self.BASE_URL}/shodan/host/{urllib.parse.quote(canonical_ip, safe=':')}?{urllib.parse.urlencode({'key': self.api_key})}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=12.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                data["is_simulated"] = False
                data["mode"] = "live_shodan"
                return data
        except Exception as e:
            details = self._mock_host_details(canonical_ip)
            details["api_warning"] = f"Live Shodan host lookup failed ({self._scrub_secret(str(e))}); showing offline fallback."
            return details

    def _matches_query(self, sample: Dict[str, Any], query: str) -> bool:
        """Honestly evaluate Shodan-style filter tokens against an RFC 5737 catalog record."""
        q = (query or "").strip()
        if not q or q == "*":
            return True

        # Tokenize preserving single/double quoted phrases
        tokens = re.findall(r'"[^"]+"|\'[^\']+\'|\S+', q)
        if not tokens:
            return True

        ports = set(sample.get("ports") or [])
        if sample.get("port"):
            ports.add(int(sample["port"]))
        loc = sample.get("location") or {}
        vulns = [str(v).lower() for v in (sample.get("vulns") or [])]
        tags = [str(t).lower() for t in (sample.get("tags") or [])]
        searchable_blob = " ".join([
            str(sample.get("ip_str", "")),
            str(sample.get("org", "")),
            str(sample.get("product", "")),
            str(sample.get("version", "")),
            str(sample.get("data", "")),
            " ".join(sample.get("hostnames") or []),
            str(loc.get("country_code", "")),
            str(loc.get("country_name", "")),
            str(loc.get("city", "")),
            " ".join(tags),
            " ".join(vulns),
        ]).lower()

        for raw_tok in tokens:
            tok = raw_tok.strip()
            if not tok:
                continue
            low = tok.lower()

            if ":" in tok and not (tok.startswith('"') or tok.startswith("'")):
                key, val = tok.split(":", 1)
                key = key.lower().strip()
                val_clean = val.strip().strip('"').strip("'").lower()

                if key == "port":
                    try:
                        if int(val_clean) not in ports:
                            return False
                    except ValueError:
                        return False
                elif key == "country":
                    cc = str(loc.get("country_code", "")).lower()
                    cn = str(loc.get("country_name", "")).lower()
                    if val_clean != cc and val_clean not in cn:
                        return False
                elif key == "city":
                    if val_clean not in str(loc.get("city", "")).lower():
                        return False
                elif key == "org":
                    if val_clean not in str(sample.get("org", "")).lower():
                        return False
                elif key == "product":
                    if val_clean not in str(sample.get("product", "")).lower() and val_clean not in searchable_blob:
                        return False
                elif key == "tag":
                    if val_clean not in tags:
                        return False
                elif key == "vuln":
                    if not any(val_clean in v for v in vulns):
                        return False
                elif key == "has_vuln":
                    want = val_clean in ("true", "1", "yes")
                    if bool(vulns) != want:
                        return False
                elif key == "has_screenshot":
                    want = val_clean in ("true", "1", "yes")
                    if bool(sample.get("has_screenshot")) != want:
                        return False
                elif key == "net":
                    try:
                        net = ipaddress.ip_network(val_clean, strict=False)
                        if ipaddress.ip_address(sample["ip_str"]) not in net:
                            return False
                    except ValueError:
                        return False
                else:
                    if val_clean and val_clean not in searchable_blob:
                        return False
            else:
                phrase = low.strip('"').strip("'")
                if phrase and phrase not in searchable_blob:
                    return False

        return True

    def _mock_search_results(self, query: str, page: int = 1, limit: int = 30) -> Dict[str, Any]:
        """Deterministic RFC 5737 sample radar dataset with honest query filtering."""
        filtered = [dict(item) for item in OFFLINE_DEMO_CATALOG if self._matches_query(item, query)]
        page_idx = max(1, int(page))
        lim = max(1, min(500, int(limit)))
        start = (page_idx - 1) * lim
        sliced = filtered[start : start + lim]

        return {
            "total": len(filtered),
            "matches": sliced,
            "live": False,
            "mode": "offline_demo",
            "is_simulated": True,
            "query": query,
        }

    def _mock_host_details(self, ip: str) -> Dict[str, Any]:
        """Consistent RFC 5737 offline host details matching catalog entries."""
        for item in OFFLINE_DEMO_CATALOG:
            if item["ip_str"] == ip:
                loc = item.get("location") or {}
                return {
                    "ip": ip,
                    "ip_str": ip,
                    "org": item.get("org"),
                    "hostnames": list(item.get("hostnames") or []),
                    "product": item.get("product"),
                    "version": item.get("version"),
                    "ports": list(item.get("ports") or [item.get("port")]),
                    "country_code": loc.get("country_code", "XX"),
                    "country_name": loc.get("country_name", "Unknown"),
                    "city": loc.get("city", ""),
                    "latitude": loc.get("latitude", 0.0),
                    "longitude": loc.get("longitude", 0.0),
                    "last_update": "2026-11-26T06:00:00.000Z",
                    "vulns": list(item.get("vulns") or []),
                    "tags": list(item.get("tags") or []),
                    "banner": item.get("data", ""),
                    "is_simulated": True,
                    "mode": "offline_demo",
                }

        return {
            "ip": ip,
            "ip_str": ip,
            "org": "Unindexed Host (Offline Demo Mode)",
            "hostnames": [],
            "product": "Live Shodan key required",
            "version": "",
            "ports": [],
            "country_code": "XX",
            "country_name": "Offline Demo",
            "city": "Not queried upstream",
            "latitude": 0.0,
            "longitude": 0.0,
            "last_update": "2026-11-26T06:00:00.000Z",
            "vulns": [],
            "tags": ["offline-demo"],
            "banner": "No cached banner in RFC 5737 offline catalog. Configure SHODAN_API_KEY for live Shodan host interrogation.",
            "is_simulated": True,
            "mode": "offline_demo",
        }
