"""Command Line Interface for agent-gods-eye.

100% Python Standard Library — Zero External Dependencies.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import threading
import time
import urllib.request

from .radar import RadarEngine
from .server import GodsEyeServer
from .shodan_client import ShodanClient
from .storage import GodsEyeStorage

# ANSI Formatting
C_GOLD = "\033[38;5;214m"
C_CYAN = "\033[38;5;51m"
C_GREEN = "\033[38;5;48m"
C_RED = "\033[38;5;196m"
C_AMBER = "\033[38;5;208m"
C_DIM = "\033[2m"
C_BOLD = "\033[1m"
C_RESET = "\033[0m"


def print_banner() -> None:
    print(f"{C_GOLD}{C_BOLD}👁️ AGENT GODS EYE v1.0.0{C_RESET}")
    print(f"{C_DIM}Autonomous Shodan OSINT Tactical Radar & 3D Planetary Cockpit{C_RESET}")
    print(f"{C_DIM}Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform{C_RESET}\n")


def cmd_serve(args: argparse.Namespace) -> None:
    print_banner()

    repo_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    public_dir = os.path.join(repo_dir, "public")
    db_path = os.path.abspath(args.db)

    shodan = ShodanClient(api_key=args.key)
    storage = GodsEyeStorage(db_path)

    has_key = shodan.has_valid_key()
    key_status = f"{C_GREEN}Active & Connected{C_RESET}" if has_key else f"{C_AMBER}Offline / Simulated Mode{C_RESET}"
    print(f"Shodan Engine: {key_status}")
    if has_key:
        info = shodan.get_api_info()
        print(f"Account Plan:  {C_GOLD}{info.get('plan', 'dev').upper()}{C_RESET} ({info.get('query_credits', 0)} query credits remaining)")

    server = GodsEyeServer(
        host=args.host,
        port=args.port,
        shodan=shodan,
        storage=storage,
        public_dir=public_dir
    )

    t = threading.Thread(target=server.serve_forever, daemon=True, name="GodsEyeServer")
    t.start()

    print(f"\n{C_CYAN}Tactical Radar Cockpit:{C_RESET} http://{args.host}:{args.port}")
    print(f"{C_DIM}3D Planetary globe & live Shodan reconnaissance stream active. (Ctrl+C to stop){C_RESET}\n")

    def shutdown(sig, frame):
        print(f"\n{C_AMBER}Halting radar deck gracefully...{C_RESET}")
        server.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    while True:
        time.sleep(1.0)


def cmd_search(args: argparse.Namespace) -> None:
    shodan = ShodanClient(api_key=args.key)
    print_banner()
    print(f"Scanning target surface for: {C_GOLD}{args.query}{C_RESET}...\n")

    raw = shodan.search(args.query, limit=args.limit)
    nodes = RadarEngine.process_search_payload(raw)

    print(f"{C_BOLD}{'IP ADDRESS':<16} {'PORT':<6} {'COUNTRY':<12} {'THREAT':<10} {'PRODUCT / SERVICE':<28}{C_RESET}")
    print("-" * 75)

    for n in nodes:
        lvl = n["threat_level"]
        color = C_RED if lvl == "CRITICAL" else (C_AMBER if lvl == "HIGH" else C_GREEN)
        ip_port = f"{n['ip']}"
        country = f"{n['country']} ({n['city'][:8]})"
        prod = f"{n['product']} {n['version']}"[:26]
        print(f"{ip_port:<16} {n['port']:<6} {country:<12} {color}{lvl:<10}{C_RESET} {prod:<28}")

    print(f"\nTotal Identified Targets: {len(nodes)}")


def cmd_status(args: argparse.Namespace) -> None:
    url = f"http://{args.host}:{args.port}/api/stats"
    try:
        with urllib.request.urlopen(url, timeout=5.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"{C_RED}Error connecting to agent-gods-eye at {url}: {e}{C_RESET}")
        sys.exit(1)

    print_banner()
    print(f"  Tracked Targets:   {C_GOLD}{data.get('total_targets', 0)}{C_RESET}")
    print(f"  Historical Scans:  {data.get('total_searches', 0)}")
    print(f"  Shodan Status:     {C_GREEN if data.get('shodan_connected') else C_AMBER}{'CONNECTED' if data.get('shodan_connected') else 'OFFLINE'}{C_RESET}")
    print("\n  Threat Breakdown:")
    for lvl, cnt in data.get("threat_distribution", {}).items():
        color = C_RED if lvl == "CRITICAL" else (C_AMBER if lvl == "HIGH" else C_GREEN)
        print(f"    • {color}{lvl:<10}{C_RESET}: {cnt}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="agent-gods-eye",
        description="Autonomous Shodan OSINT tactical radar and 3D planetary intelligence cockpit."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # serve
    p_serve = subparsers.add_parser("serve", help="Launch Web Deck & REST API")
    p_serve.add_argument("--host", default="0.0.0.0")
    p_serve.add_argument("--port", type=int, default=8112)
    p_serve.add_argument("--db", default="godseye.db")
    p_serve.add_argument("--key", default=None, help="Shodan API key override")

    # search
    p_search = subparsers.add_parser("search", help="Execute an OSINT scan query")
    p_search.add_argument("query", help="Shodan query string (e.g. 'port:554 has_screenshot:true')")
    p_search.add_argument("--limit", type=int, default=20)
    p_search.add_argument("--key", default=None)

    # status
    p_status = subparsers.add_parser("status", help="Inspect status of running radar daemon")
    p_status.add_argument("--host", default="127.0.0.1")
    p_status.add_argument("--port", type=int, default=8112)

    args = parser.parse_args()

    if args.command == "serve":
        cmd_serve(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "status":
        cmd_status(args)


if __name__ == "__main__":
    main()
