"""Radar Engine for Normalizing Shodan OSINT and Computing 3D Globe Coordinates.

100% Python Standard Library — Zero External Dependencies.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class TargetNode:
    """Normalized OSINT target coordinate for 3D planetary rendering and tabular display."""
    ip: str
    port: int
    transport: str
    org: str
    hostname: str
    country: str
    country_name: str
    city: str
    latitude: float
    longitude: float
    # 3D Unit Sphere Cartesian Coordinates for WebGL / Canvas Orbital Globe
    x: float
    y: float
    z: float
    product: str
    version: str
    banner_snippet: str
    vulns: List[str]
    category: str
    threat_level: str
    threat_score: int


class RadarEngine:
    """Processes raw Shodan intelligence into tactile 3D planetary radar telemetry."""

    @staticmethod
    def lat_lon_to_cartesian(lat: float, lon: float, radius: float = 1.0) -> Tuple[float, float, float]:
        """Convert latitude and longitude into 3D unit sphere Cartesian coordinates (x, y, z)."""
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)

        x = round(radius * math.cos(lat_rad) * math.sin(lon_rad), 4)
        y = round(radius * math.sin(lat_rad), 4)
        z = round(radius * math.cos(lat_rad) * math.cos(lon_rad), 4)
        return (x, y, z)

    @classmethod
    def evaluate_threat(cls, port: int, product: str, banner: str, vulns: List[str]) -> Tuple[str, str, int]:
        """Calculate threat score (0-100), level, and target category."""
        score = 15  # baseline exposure score
        category = "NETWORK_INFRASTRUCTURE"

        p_lower = (product or "").lower()
        b_lower = (banner or "").lower()

        # Category & Port identification
        if port == 554 or "rtsp" in p_lower or "camera" in b_lower or "h.264" in b_lower or "ipcam" in b_lower:
            category = "SURVEILLANCE_CAMERA"
            score += 35
        elif port in (502, 102, 47808) or "modbus" in b_lower or "scada" in b_lower or "siemens" in b_lower:
            category = "SCADA_INDUSTRIAL"
            score += 45
        elif port in (5900, 5901) or "vnc" in p_lower or "rfb" in b_lower:
            category = "REMOTE_DESKTOP"
            score += 40
        elif port in (3389, 22, 23):
            category = "REMOTE_ACCESS"
            score += 30
        elif port in (6379, 9200, 27017, 5432, 3306):
            category = "DATABASE_CLUSTER"
            score += 35
        elif port in (8080, 8443, 80, 443):
            category = "WEB_INTERFACE"
            score += 15

        # Unauthenticated indicators
        if "security types: none" in b_lower or "noauth" in b_lower or "200 ok" in b_lower:
            score += 20

        # CVEs
        if vulns:
            score += min(35, len(vulns) * 15)

        score = min(100, max(5, score))

        if score >= 75:
            level = "CRITICAL"
        elif score >= 50:
            level = "HIGH"
        elif score >= 30:
            level = "ELEVATED"
        else:
            level = "LOW"

        return category, level, score

    @classmethod
    def normalize_match(cls, raw: Dict[str, Any]) -> TargetNode:
        """Transform raw Shodan match dictionary into normalized TargetNode."""
        ip = str(raw.get("ip_str") or raw.get("ip") or "0.0.0.0")
        port = int(raw.get("port") or 0)
        transport = str(raw.get("transport") or "tcp")
        org = str(raw.get("org") or raw.get("isp") or "Unknown Organization")
        
        hostnames = raw.get("hostnames", [])
        hostname = hostnames[0] if (hostnames and isinstance(hostnames, list)) else ip

        loc = raw.get("location") or {}
        country = str(loc.get("country_code") or "XX")
        country_name = str(loc.get("country_name") or "Global Target")
        city = str(loc.get("city") or "Unspecified Location")
        lat = float(loc.get("latitude") or 0.0)
        lon = float(loc.get("longitude") or 0.0)

        # 3D coordinates
        x, y, z = cls.lat_lon_to_cartesian(lat, lon)

        product = str(raw.get("product") or raw.get("_shodan", {}).get("module") or "Unknown Service")
        version = str(raw.get("version") or "")

        data_str = str(raw.get("data") or "")
        snippet = " ".join(data_str.split())[:120]

        vulns_dict = raw.get("vulns")
        vulns_list: List[str] = []
        if isinstance(vulns_dict, dict):
            vulns_list = list(vulns_dict.keys())
        elif isinstance(vulns_dict, list):
            vulns_list = [str(v) for v in vulns_dict]

        category, level, score = cls.evaluate_threat(port, product, data_str, vulns_list)

        return TargetNode(
            ip=ip,
            port=port,
            transport=transport,
            org=org,
            hostname=hostname,
            country=country,
            country_name=country_name,
            city=city,
            latitude=lat,
            longitude=lon,
            x=x,
            y=y,
            z=z,
            product=product,
            version=version,
            banner_snippet=snippet,
            vulns=vulns_list,
            category=category,
            threat_level=level,
            threat_score=score
        )

    @classmethod
    def process_search_payload(cls, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert matches from Shodan search payload into list of dictionaries."""
        matches = payload.get("matches", [])
        nodes: List[Dict[str, Any]] = []
        for m in matches:
            if isinstance(m, dict):
                node = cls.normalize_match(m)
                nodes.append(asdict(node))
        return nodes
