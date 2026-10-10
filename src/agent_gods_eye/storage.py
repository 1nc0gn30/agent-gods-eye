"""SQLite Storage and Real-time SSE PubSub for Gods Eye Radar.

100% Python Standard Library — Zero External Dependencies.
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
                            first_seen TEXT NOT NULL,
                            last_seen TEXT NOT NULL,
                            PRIMARY KEY (ip, port)
                        );
                    """)
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

    def log_search(self, query: str, total_hits: int, returned_count: int) -> int:
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    cur = conn.execute("""
                        INSERT INTO searches (timestamp, query, total_hits, returned_count)
                        VALUES (?, ?, ?, ?)
                    """, (now_iso, query, total_hits, returned_count))
                    search_id = cur.lastrowid
            finally:
                conn.close()

        self.broadcast_event("search", {
            "query": query,
            "total_hits": total_hits,
            "returned_count": returned_count,
            "timestamp": now_iso
        })
        return search_id

    def upsert_targets(self, nodes: List[Dict[str, Any]]) -> int:
        """Insert or update target nodes in registry."""
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        count = 0
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    for n in nodes:
                        conn.execute("""
                            INSERT INTO targets (
                                ip, port, org, hostname, country, country_name,
                                city, latitude, longitude, category, threat_level,
                                threat_score, product, first_seen, last_seen
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(ip, port) DO UPDATE SET
                                org = excluded.org,
                                hostname = excluded.hostname,
                                threat_score = excluded.threat_score,
                                threat_level = excluded.threat_level,
                                last_seen = excluded.last_seen;
                        """, (
                            n["ip"], n["port"], n.get("org"), n.get("hostname"),
                            n.get("country"), n.get("country_name"), n.get("city"),
                            n.get("latitude"), n.get("longitude"), n.get("category"),
                            n.get("threat_level"), n.get("threat_score"), n.get("product"),
                            now_iso, now_iso
                        ))
                        count += 1
            finally:
                conn.close()

        self.broadcast_event("targets_updated", {"count": count, "timestamp": now_iso})
        return count

    def get_stats(self) -> Dict[str, Any]:
        """Aggregate statistical distribution of monitored targets."""
        with self._lock:
            conn = self._get_connection()
            try:
                total_targets = conn.execute("SELECT COUNT(*) FROM targets;").fetchone()[0]
                total_searches = conn.execute("SELECT COUNT(*) FROM searches;").fetchone()[0]
                
                # Threat level breakdown
                threat_rows = conn.execute("""
                    SELECT threat_level, COUNT(*) as cnt 
                    FROM targets 
                    GROUP BY threat_level 
                    ORDER BY cnt DESC;
                """).fetchall()
                threat_dist = {r["threat_level"]: r["cnt"] for r in threat_rows}

                # Category breakdown
                cat_rows = conn.execute("""
                    SELECT category, COUNT(*) as cnt 
                    FROM targets 
                    GROUP BY category 
                    ORDER BY cnt DESC;
                """).fetchall()
                cat_dist = {r["category"]: r["cnt"] for r in cat_rows}

                # Top countries
                country_rows = conn.execute("""
                    SELECT country, country_name, COUNT(*) as cnt 
                    FROM targets 
                    GROUP BY country 
                    ORDER BY cnt DESC LIMIT 10;
                """).fetchall()
                top_countries = [dict(r) for r in country_rows]

                return {
                    "total_targets": total_targets,
                    "total_searches": total_searches,
                    "threat_distribution": threat_dist,
                    "category_distribution": cat_dist,
                    "top_countries": top_countries
                }
            finally:
                conn.close()

    def get_recent_targets(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.execute("""
                    SELECT ip, port, org, hostname, country, country_name,
                           city, latitude, longitude, category, threat_level,
                           threat_score, product, last_seen
                    FROM targets
                    ORDER BY threat_score DESC, last_seen DESC LIMIT ?
                """, (limit,))
                rows = cur.fetchall()
                return [dict(r) for r in rows]
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
