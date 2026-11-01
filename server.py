#!/usr/bin/env python3
"""Agent God's Eye - Standalone Server Daemon.

Engineered by 1nc0gn30 (@1nc0gn30) • NullAI Platform.
100% Python Standard Library — Zero External Dependencies.
"""

from __future__ import annotations

import argparse
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(SCRIPT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from agent_gods_eye.cli import cmd_serve


def main():
    parser = argparse.ArgumentParser(description="Agent God's Eye Server")
    parser.add_argument("--port", type=int, default=8112, help="Web Cockpit Port (default 8112)")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface (default 127.0.0.1)")
    parser.add_argument("--db", default=os.path.join(SCRIPT_DIR, "godseye.db"), help="SQLite database path")
    parser.add_argument("--key", default=None, help="Shodan API key override")

    args = parser.parse_args()
    cmd_serve(args)


if __name__ == "__main__":
    main()
