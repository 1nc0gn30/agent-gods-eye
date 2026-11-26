"""SQLite Storage and Real-time SSE PubSub for Gods Eye Radar.

100% Python Standard Library — Zero External Dependencies.
Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform.
"""

from __future__ import annotations

import datetime
import json
import queue
import sqlite3
import threading
from typing import Any, Dict, List, Optional


class GodsEyeStorage:
    """Thread-safe SQLite store for target registry, historical queries, and live radar events."""

    def __init__(self, db_path: str = "godseye.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._sse_queues: List[queue.Queue] = []
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self) -> None:
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS searches (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            timestamp TEXT NOT NULL,
                            query TEXT NOT NULL,
                            total_hits INTEGER NOT NULL,
                            returned_count INTEGER NOT NULL
                        );
                    """)
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS targets (
                            ip TEXT NOT NULL,
                            port INTEGER NOT NULL,
                            org TEXT,
                            hostname TEXT,
                            country TEXT,
                            country_name TEXT,
                            city TEXT,
                            latitude REAL,
                            longitude REAL,
                            category TEXT,
                            threat_level TEXT,
                            threat_score INTEGER,
                            product TEXT,
                            ports_json TEXT,
                            vulns_json TEXT,
                            tags_json TEXT,
                            banner_snippet TEXT,
                            is_simulated INTEGER NOT NULL DEFAULT 0,
                            first_seen TEXT NOT NULL,
                            last_seen TEXT NOT NULL,
                            PRIMARY KEY (ip, port)
                        );
                    """)
                    # Safe migration for pre-existing SQLite schemas
                    existing_cols = {
                        row["name"]
                        for row in conn.execute("PRAGMA table_info(targets);").fetchall()
                    }
                    migrations = {
                        "ports_json": "ALTER TABLE targets ADD COLUMN ports_json TEXT;",
                        "vulns_json": "ALTER TABLE targets ADD COLUMN vulns_json TEXT;",
                        "tags_json": "ALTER TABLE targets ADD COLUMN tags_json TEXT;",
                        "banner_snippet": "ALTER TABLE targets ADD COLUMN banner_snippet TEXT;",
                        "is_simulated": "ALTER TABLE targets ADD COLUMN is_simulated INTEGER NOT NULL DEFAULT 0;",
                    }
                    for col, ddl in migrations.items():
                        if col not in existing_cols:
                            conn.execute(ddl)

                    conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_targets_country ON targets(country);
                    """)
                    conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_targets_threat ON targets(threat_score);
                    """)
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS radar_events (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            timestamp TEXT NOT NULL,
                            event_type TEXT NOT NULL,
                            message TEXT NOT NULL,
                            data_json TEXT
                        );
                    """)
            finally:
                conn.close()

    def log_event(self, event_type: str, message: str, data: Optional[Dict[str, Any]] = None) -> int:
        """Persist a radar telemetry event into radar_events."""
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        payload_json = json.dumps(data or {})
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    cur = conn.execute(
                        """
                        INSERT INTO radar_events (timestamp, event_type, message, data_json)
                        VALUES (?, ?, ?, ?)
                        """,
                        (now_iso, event_type, message, payload_json),
                    )
                    return int(cur.lastrowid or 0)
            finally:
                conn.close()

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return recent persisted radar telemetry events."""
        lim = max(1, min(500, int(limit)))
        with self._lock:
            conn = self._get_connection()
            try:
                rows = conn.execute(
                    """
                    SELECT id, timestamp, event_type, message, data_json
                    FROM radar_events
                    ORDER BY id DESC LIMIT ?
                    """,
                    (lim,),
                ).fetchall()
                events: List[Dict[str, Any]] = []
                for r in rows:
                    try:
                        parsed = json.loads(r["data_json"]) if r["data_json"] else {}
                    except Exception:
                        parsed = {}
                    events.append({
                        "id": r["id"],
                        "timestamp": r["timestamp"],
                        "event_type": r["event_type"],
                        "message": r["message"],
                        "data": parsed,
                    })
                return events
            finally:
                conn.close()

    def log_search(self, query: str, total_hits: int, returned_count: int, is_simulated: bool = False) -> int:
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    cur = conn.execute(
                        """
                        INSERT INTO searches (timestamp, query, total_hits, returned_count)
                        VALUES (?, ?, ?, ?)
                        """,
                        (now_iso, query, total_hits, returned_count),
                    )
                    search_id = int(cur.lastrowid or 0)
            finally:
                conn.close()

        payload = {
            "query": query,
            "total_hits": total_hits,
            "returned_count": returned_count,
            "is_simulated": is_simulated,
            "timestamp": now_iso,
        }
        mode_tag = "RFC 5737 Demo" if is_simulated else "Live Shodan"
        self.log_event("search", f"[{mode_tag}] Query '{query}' matched {returned_count}/{total_hits} hosts", payload)
        self.broadcast_event("search", payload)
        return search_id

    def upsert_targets(self, nodes: List[Dict[str, Any]]) -> int:
        """Insert or update target nodes in registry, preserving is_simulated flag."""
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        count = 0
        sim_count = 0
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    for n in nodes:
                        port_val = int(n.get("port") or 0)
                        ports_list = n.get("ports")
                        if not isinstance(ports_list, list) or not ports_list:
                            ports_list = [port_val] if port_val else []
                        vulns_list = n.get("vulns") if isinstance(n.get("vulns"), list) else []
                        tags_list = n.get("tags") if isinstance(n.get("tags"), list) else []
                        is_sim = 1 if n.get("is_simulated") else 0
                        if is_sim:
                            sim_count += 1

                        conn.execute(
                            """
                            INSERT INTO targets (
                                ip, port, org, hostname, country, country_name,
                                city, latitude, longitude, category, threat_level,
                                threat_score, product, ports_json, vulns_json, tags_json,
                                banner_snippet, is_simulated, first_seen, last_seen
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(ip, port) DO UPDATE SET
                                org = excluded.org,
                                hostname = excluded.hostname,
                                country = excluded.country,
                                country_name = excluded.country_name,
                                city = excluded.city,
                                latitude = excluded.latitude,
                                longitude = excluded.longitude,
                                category = excluded.category,
                                threat_score = excluded.threat_score,
                                threat_level = excluded.threat_level,
                                product = excluded.product,
                                ports_json = excluded.ports_json,
                                vulns_json = excluded.vulns_json,
                                tags_json = excluded.tags_json,
                                banner_snippet = excluded.banner_snippet,
                                is_simulated = excluded.is_simulated,
                                last_seen = excluded.last_seen;
                            """,
                            (
                                n["ip"],
                                port_val,
                                n.get("org"),
                                n.get("hostname"),
                                n.get("country"),
                                n.get("country_name"),
                                n.get("city"),
                                n.get("latitude"),
                                n.get("longitude"),
                                n.get("category"),
                                n.get("threat_level"),
                                n.get("threat_score"),
                                n.get("product"),
                                json.dumps(ports_list),
                                json.dumps(vulns_list),
                                json.dumps(tags_list),
                                n.get("banner_snippet") or n.get("banner") or "",
                                is_sim,
                                now_iso,
                                now_iso,
                            ),
                        )
                        count += 1
            finally:
                conn.close()

        payload = {
            "count": count,
            "simulated_count": sim_count,
            "live_count": count - sim_count,
            "timestamp": now_iso,
        }
        if count > 0:
            self.log_event("targets_updated", f"Cataloged {count} radar targets ({sim_count} simulated)", payload)
            self.broadcast_event("targets_updated", payload)
        return count

    def _hydrate_row(self, row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        port_val = d.get("port")
        try:
            ports = json.loads(d.pop("ports_json", None) or "[]")
        except Exception:
            ports = []
        if not ports and port_val:
            ports = [int(port_val)]
        try:
            vulns = json.loads(d.pop("vulns_json", None) or "[]")
        except Exception:
            vulns = []
        try:
            tags = json.loads(d.pop("tags_json", None) or "[]")
        except Exception:
            tags = []

        d["ports"] = ports
        d["vulns"] = vulns
        d["tags"] = tags
        d["is_simulated"] = bool(d.get("is_simulated", 0))
        return d

    def get_stats(self) -> Dict[str, Any]:
        """Aggregate statistical distribution of monitored targets."""
        with self._lock:
            conn = self._get_connection()
            try:
                total_targets = conn.execute("SELECT COUNT(*) FROM targets;").fetchone()[0]
                simulated_targets = conn.execute("SELECT COUNT(*) FROM targets WHERE is_simulated = 1;").fetchone()[0]
                live_targets = total_targets - simulated_targets
                total_searches = conn.execute("SELECT COUNT(*) FROM searches;").fetchone()[0]
                unique_countries = conn.execute(
                    "SELECT COUNT(DISTINCT country) FROM targets WHERE country IS NOT NULL AND country != '';"
                ).fetchone()[0]

                threat_rows = conn.execute("""
                    SELECT threat_level, COUNT(*) as cnt
                    FROM targets
                    GROUP BY threat_level
                    ORDER BY cnt DESC;
                """).fetchall()
                threat_dist = {r["threat_level"]: r["cnt"] for r in threat_rows}

                cat_rows = conn.execute("""
                    SELECT category, COUNT(*) as cnt
                    FROM targets
                    GROUP BY category
                    ORDER BY cnt DESC;
                """).fetchall()
                cat_dist = {r["category"]: r["cnt"] for r in cat_rows}

                country_rows = conn.execute("""
                    SELECT country, country_name, COUNT(*) as cnt
                    FROM targets
                    GROUP BY country
                    ORDER BY cnt DESC LIMIT 10;
                """).fetchall()
                top_countries = [dict(r) for r in country_rows]

                return {
                    "total_targets": total_targets,
                    "total_nodes": total_targets,
                    "live_targets": live_targets,
                    "simulated_targets": simulated_targets,
                    "total_searches": total_searches,
                    "high_threat_nodes": threat_dist.get("CRITICAL", 0) + threat_dist.get("HIGH", 0),
                    "unique_countries": unique_countries,
                    "threat_distribution": threat_dist,
                    "category_distribution": cat_dist,
                    "top_countries": top_countries,
                }
            finally:
                conn.close()

    def get_recent_targets(self, limit: int = 50, include_simulated: bool = True) -> List[Dict[str, Any]]:
        lim = max(1, min(1000, int(limit)))
        with self._lock:
            conn = self._get_connection()
            try:
                where_clause = "" if include_simulated else "WHERE is_simulated = 0"
                cur = conn.execute(
                    f"""
                    SELECT ip, port, org, hostname, country, country_name,
                           city, latitude, longitude, category, threat_level,
                           threat_score, product, ports_json, vulns_json, tags_json,
                           banner_snippet, is_simulated, last_seen
                    FROM targets
                    {where_clause}
                    ORDER BY threat_score DESC, last_seen DESC LIMIT ?
                    """,
                    (lim,),
                )
                return [self._hydrate_row(r) for r in cur.fetchall()]
            finally:
                conn.close()

    def get_targets_by_ip(self, ip: str) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.execute(
                    """
                    SELECT ip, port, org, hostname, country, country_name,
                           city, latitude, longitude, category, threat_level,
                           threat_score, product, ports_json, vulns_json, tags_json,
                           banner_snippet, is_simulated, last_seen
                    FROM targets
                    WHERE ip = ?
                    ORDER BY threat_score DESC, last_seen DESC
                    """,
                    (ip,),
                )
                return [self._hydrate_row(r) for r in cur.fetchall()]
            finally:
                conn.close()

    # --- SSE PubSub ---
    def subscribe_sse(self) -> queue.Queue:
        q: queue.Queue = queue.Queue(maxsize=100)
        with self._lock:
            self._sse_queues.append(q)
        return q

    def unsubscribe_sse(self, q: queue.Queue) -> None:
        with self._lock:
            if q in self._sse_queues:
                self._sse_queues.remove(q)

    def broadcast_event(self, event_name: str, payload: Dict[str, Any]) -> None:
        with self._lock:
            queues = list(self._sse_queues)
        msg = f"event: {event_name}\ndata: {json.dumps(payload)}\n\n"
        for q in queues:
            try:
                q.put_nowait(msg)
            except queue.Full:
                pass
