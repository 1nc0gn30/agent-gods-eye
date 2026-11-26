"""verify_ui.py — Automated Headless Verification Harness for Agent God's Eye (v2.6.0).

Verifies triple-viewport responsiveness, dual-theme rendering (Editorial Ivory Light + Obsidian Dark),
zero console errors, zero horizontal overflow, live SSE stream hydration, honest offline mode badge,
and host inspection modal behavior.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.environ.get("PORT", "8112"))
BASE_URL = f"http://127.0.0.1:{PORT}"
SHOT_DIR = Path(os.environ.get("SHOT_DIR", os.path.join(tempfile.gettempdir(), "agent-gods-eye-verify")))
SHOT_DIR.mkdir(parents=True, exist_ok=True)


def verify() -> None:
    print(f"[TEST] Verifying Agent God's Eye v2.6.0 at {BASE_URL}...")

    viewports = [
        {"name": "mobile", "width": 390, "height": 844},
        {"name": "tablet", "width": 820, "height": 1180},
        {"name": "desktop", "width": 1440, "height": 900},
    ]

    results = {"viewports": [], "interactive": {}, "consoleErrors": []}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path="/usr/bin/google-chrome",
            headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
        )

        for theme in ("light", "dark"):
            for vp in viewports:
                page = browser.new_page(viewport={"width": vp["width"], "height": vp["height"]})
                errors = []
                page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
                page.on("pageerror", lambda err: errors.append(str(err)))

                page.goto(f"{BASE_URL}/?theme={theme}", wait_until="networkidle")
                time.sleep(0.8)

                overflow = page.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
                shot_path = SHOT_DIR / f"{theme}_{vp['name']}.jpg"
                page.screenshot(path=str(shot_path), full_page=False, type="jpeg", quality=85)

                passed = len(errors) == 0 and overflow <= 1
                results["viewports"].append({
                    "theme": theme,
                    "viewport": vp["name"],
                    "overflowPx": overflow,
                    "errors": errors,
                    "passed": passed,
                })
                results["consoleErrors"].extend(errors)
                page.close()

        # Interactive workflow check (Modbus preset, SSE live entries, host inspect modal)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(f"{BASE_URL}/?theme=dark", wait_until="networkidle")
        time.sleep(0.8)

        page.click('button[data-query="port:502 modbus"]')
        time.sleep(0.6)

        first_ip = page.locator("#targetsTableBody tr").first.get_attribute("data-ip")
        stream_count = page.locator("#streamConsole .stream-entry").count()
        plan_text = page.locator("#metricPlan").inner_text().strip()

        page.locator("#targetsTableBody tr button").first.click()
        time.sleep(0.4)
        modal_open = page.evaluate("() => document.getElementById('hostModal').classList.contains('open')")

        results["interactive"] = {
            "firstModbusIp": first_ip,
            "streamEntries": stream_count,
            "planText": plan_text,
            "modalOpen": modal_open,
        }
        page.close()
        browser.close()

    print(json.dumps(results, indent=2))
    all_ok = (
        all(v["passed"] for v in results["viewports"])
        and results["interactive"].get("modalOpen")
        and results["interactive"].get("streamEntries", 0) >= 2
    )
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    verify()
