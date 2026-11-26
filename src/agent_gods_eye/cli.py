"""Command Line Interface for agent-gods-eye.

100% Python Standard Library — Zero External Dependencies.
Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform.
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

from .mcp_server import GodsEyeMCPServer
from .radar import RadarEngine
from .server import GodsEyeServer
from .shodan_client import ShodanClient, VERSION, validate_public_ip
from .storage import GodsEyeStorage


def _default_bind_host() -> str:
    """Bind address: localhost unless explicitly opted in via $ZOTH_BIND_HOST or
    $HOST (IP literal only; zsh sets HOST to the hostname) or --host."""
    import ipaddress
    for var in ("ZOTH_BIND_HOST", "HOST"):
        val = os.environ.get(var, "").strip()
        if val == "localhost":
            return "127.0.0.1"
        if val:
            try:
                ipaddress.ip_address(val)
                return val
            except ValueError:
                pass
    return "127.0.0.1"


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
    print(f"{C_GOLD}{C_BOLD}👁️ AGENT GOD'S EYE v{VERSION}{C_RESET}")
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
    key_status = f"{C_GREEN}Live Shodan API Configured{C_RESET}" if has_key else f"{C_AMBER}Offline Demo Mode (RFC 5737 Catalog){C_RESET}"
    print(f"Shodan Engine: {key_status}")
    if has_key:
        info = shodan.get_api_info()
        print(f"Account Plan:  {C_GOLD}{str(info.get('plan', 'dev')).upper()}{C_RESET} ({info.get('query_credits', 0)} query credits remaining)")

    server = GodsEyeServer(
        host=args.host,
        port=args.port,
        shodan=shodan,
        storage=storage,
        public_dir=public_dir,
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
    raw = shodan.search(args.query, limit=max(1, min(500, args.limit)))
    nodes = RadarEngine.process_search_payload(raw)
    is_sim = bool(raw.get("is_simulated", not raw.get("live", False)))

    if getattr(args, "json", False):
        print(json.dumps({
            "version": VERSION,
            "query": args.query,
            "live": bool(raw.get("live", False)),
            "mode": raw.get("mode", "offline_demo" if is_sim else "live_shodan"),
            "is_simulated": is_sim,
            "total": raw.get("total", len(nodes)),
            "count": len(nodes),
            "targets": nodes,
        }, indent=2))
        return

    print_banner()
    if is_sim:
        print(f"{C_AMBER}[OFFLINE DEMO MODE]{C_RESET} No Shodan API key configured — filtering RFC 5737 documentation catalog.")
    print(f"Scanning target surface for: {C_GOLD}{args.query}{C_RESET}...\n")

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


def cmd_host(args: argparse.Namespace) -> None:
    canonical_ip, err, _code = validate_public_ip(args.ip)
    if err or not canonical_ip:
        if getattr(args, "json", False):
            print(json.dumps({"ok": False, "error": err}, indent=2))
        else:
            print(f"{C_RED}Rejected target IP '{args.ip}': {err}{C_RESET}", file=sys.stderr)
        sys.exit(2)

    shodan = ShodanClient(api_key=args.key)
    details = shodan.host(canonical_ip)
    if getattr(args, "json", False):
        print(json.dumps(details, indent=2))
        return

    print_banner()
    print(f"Host:    {C_CYAN}{details.get('ip_str', canonical_ip)}{C_RESET}")
    print(f"Org:     {details.get('org', 'Unknown')}")
    print(f"Mode:    {details.get('mode', 'offline_demo')}")
    print(f"Ports:   {', '.join(str(p) for p in details.get('ports', [])) or 'None'}")
    print(f"CVEs:    {', '.join(details.get('vulns', [])) or 'None'}")


def cmd_status(args: argparse.Namespace) -> None:
    url = f"http://{args.host}:{args.port}/api/stats"
    try:
        with urllib.request.urlopen(url, timeout=5.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        if getattr(args, "json", False):
            print(json.dumps({"ok": False, "version": VERSION, "url": url, "error": str(e)}))
            return
        print(f"{C_RED}Error connecting to agent-gods-eye at {url}: {e}{C_RESET}")
        sys.exit(1)

    if getattr(args, "json", False):
        print(json.dumps({"ok": True, "version": VERSION, "url": url, "stats": data}, indent=2))
        return

    print_banner()
    print(f"  Tracked Targets:   {C_GOLD}{data.get('total_targets', 0)}{C_RESET}")
    print(f"  Historical Scans:  {data.get('total_searches', 0)}")
    print(f"  Unique Countries:  {data.get('unique_countries', 0)}")
    print(f"  Shodan Status:     {C_GREEN if data.get('shodan_connected') else C_AMBER}{'LIVE SHODAN' if data.get('shodan_connected') else 'OFFLINE DEMO'}{C_RESET}")
    print("\n  Threat Breakdown:")
    for lvl, cnt in data.get("threat_distribution", {}).items():
        color = C_RED if lvl == "CRITICAL" else (C_AMBER if lvl == "HIGH" else C_GREEN)
        print(f"    • {color}{lvl:<10}{C_RESET}: {cnt}")
    print()


def cmd_mcp(args: argparse.Namespace) -> None:
    db_path = os.path.abspath(args.db)
    srv = GodsEyeMCPServer(db_path=db_path, api_key=args.key)
    srv.serve_stdio()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="agent-gods-eye",
        description=f"Agent God's Eye v{VERSION} — Autonomous Shodan OSINT tactical radar and 3D planetary intelligence cockpit.",
        epilog="Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform",
    )
    parser.add_argument("-v", "--version", action="version", version=f"agent-gods-eye {VERSION}")
    parser.add_argument("--status", action="store_true", help="Inspect status of running radar daemon")
    parser.add_argument("--json", action="store_true", help="Emit raw stats as JSON")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8112)

    subparsers = parser.add_subparsers(dest="command", required=False)

    # serve
    p_serve = subparsers.add_parser("serve", help="Launch Web Deck & REST API")
    p_serve.add_argument("--host", default=_default_bind_host(), help="Host interface (default: 127.0.0.1 or $ZOTH_BIND_HOST)")
    p_serve.add_argument("--port", type=int, default=8112)
    p_serve.add_argument("--db", default="godseye.db")
    p_serve.add_argument("--key", default=None, help="Shodan API key override (prefer SHODAN_API_KEY env var)")

    # search
    p_search = subparsers.add_parser("search", help="Execute an OSINT scan query")
    p_search.add_argument("query", help="Shodan query string (e.g. 'port:502 modbus')")
    p_search.add_argument("--limit", type=int, default=20, help="Max results to return (1..500, default: 20)")
    p_search.add_argument("--json", action="store_true", help="Emit machine-readable JSON search output")
    p_search.add_argument("--key", default=None, help="Shodan API key override (prefer SHODAN_API_KEY env var)")

    # host
    p_host = subparsers.add_parser("host", help="Inspect a validated public or RFC 5737 IP address")
    p_host.add_argument("ip", help="Target IP address")
    p_host.add_argument("--json", action="store_true", help="Emit machine-readable JSON host details")
    p_host.add_argument("--key", default=None, help="Shodan API key override (prefer SHODAN_API_KEY env var)")

    # status
    p_status = subparsers.add_parser("status", help="Inspect status of running radar daemon")
    p_status.add_argument("--host", default="127.0.0.1")
    p_status.add_argument("--port", type=int, default=8112)
    p_status.add_argument("--json", action="store_true", help="Emit raw stats as JSON (machine-readable)")

    # mcp
    p_mcp = subparsers.add_parser("mcp", help="Run zero-dependency JSON-RPC 2.0 stdio MCP server")
    p_mcp.add_argument("--db", default="godseye.db", help="SQLite database path")
    p_mcp.add_argument("--key", default=None, help="Shodan API key override (prefer SHODAN_API_KEY env var)")

    args = parser.parse_args()

    if getattr(args, "status", False) or (getattr(args, "json", False) and not args.command):
        cmd_status(args)
        return

    if args.command == "serve":
        cmd_serve(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "host":
        cmd_host(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "mcp":
        cmd_mcp(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
