<div align="center">
  <img src="assets/hero-banner.svg" alt="Agent God&#x27;s Eye — Sovereign Architecture Banner" width="100%" />
</div>

<br />

<div align="center">
  <a href="https://zoth.nullai.tech/tools/agent-gods-eye"><img src="https://img.shields.io/badge/Zoth_Studio_v2-Workspace-D4AF37?style=for-the-badge&logo=sparkles&logoColor=black" alt="Zoth Studio Workspace" /></a>
  <a href="https://zothos.nullai.tech"><img src="https://img.shields.io/badge/ZothOS_v3.3-Port_:8112-38BDF8?style=for-the-badge&logo=linux&logoColor=black" alt="Port :8112" /></a>
  <a href="https://nullai.tech"><img src="https://img.shields.io/badge/Security-100%25_Zero--Egress-10B981?style=for-the-badge&logo=shield&logoColor=black" alt="Zero Egress" /></a>
</div>

# ⚡ Agent God's Eye

> **Autonomous zero-dependency Shodan OSINT tactical radar, 3D kinetic planetary attack surface reconnaissance, and threat scoring.**

---

## 🏛️ Architectural Overview

**Agent God's Eye** is an official sovereign tool in the **[Zoth Studio v2](https://zoth.nullai.tech)** (72-Tool Matrix) and **[ZothOS Linux 3.3](https://zothos.nullai.tech)** ecosystem, engineered by **1nc0gn30 • NullAI ([@1nc0gn30](https://github.com/1nc0gn30))**.

| Property | Specification |
| :--- | :--- |
| **Tool ID** | `agent-gods-eye` |
| **Category** | `Security & Recon` |
| **Loopback Port** | `http://127.0.0.1:8112` |
| **Execution Mode** | `python3 server.py --port 8112` |
| **Zoth Studio Route** | [`https://zoth.nullai.tech/tools/agent-gods-eye`](https://zoth.nullai.tech/tools/agent-gods-eye) |

---

## 📖 What It Does

- **Real-Time Shodan & OSINT Surface Radar**: Scans target IP addresses, domains, and ASN blocks using Shodan API telemetry to detect exposed ports, unauthenticated industrial protocols, vulnerable services, and DNS records.
- **Autonomous Threat Scoring & Analysis**: Calculates CVSS scores and risk weights for target perimeters, classifying vulnerabilities into Critical, High, Medium, and Low vectors.
- **Interactive Planetary Visualizer**: Visualizes target coordinates, hops, open ports, and certificates on an interactive tactical canvas.
- **100% Free & Open-Access**: Zero paywalls, zero license locks, zero telemetry leaks.

---

## ⚙️ How It Works

1. **Standalone Enclave (`127.0.0.1:8112`)**: Serves an interactive responsive dashboard backed by `server.py` with real `/health`, `/api/stats`, and `/api/scan` endpoints.
2. **God-Mode Studio Component**: Integrated directly into Zoth Studio v2 (`/tools/agent-gods-eye`) with multi-pane telemetry, scan controls, and export options.
3. **ZothOS CLI (`agent-gods-eye`)**: A robust terminal tool supporting automated security pipeline audits and JSON telemetry streaming.

---

## 💻 ZothOS CLI & MCP Commands

```bash
# Check status and health
agent-gods-eye --status
agent-gods-eye status

# Output telemetry in JSON format
agent-gods-eye --json

# Run an OSINT scan against a host or domain
agent-gods-eye scan 1.1.1.1
agent-gods-eye scan example.com --json

# Launch the standalone workstation server
python3 server.py --port 8112
```

---

## ☕ Support 1nc0gn30 • NullAI & NullAI

Agent God's Eye is 100% free, open-source, and sovereign software with zero paywalls. If this tool brings you value, consider supporting our ongoing development:

- **☕ Buy Us a Coffee (Stripe)**: [buy.stripe.com/3cIfZg27PdKo2D64Ocfw40X](https://buy.stripe.com/3cIfZg27PdKo2D64Ocfw40X)
- **◎ Solana Tip Address**: `GG2eQbVh8ut1BK6j1A2tz7pSySdLpD38BgyEhGcxdXoK`

---

<div align="center">
  <sub>Engineered by <b>1nc0gn30 • NullAI</b> (<a href="https://github.com/1nc0gn30">@1nc0gn30</a>) &bull; <a href="https://nullai.tech">NullAI Platform</a> &bull; <a href="https://zoth.nullai.tech">Zoth Studio v2</a></sub>
</div>

---

## 🏛️ ZothOS v3.4, Zoth Studio v2 & Obsidian Second Brain Ecosystem

```mermaid
flowchart LR
    subgraph ZothOS["🐧 ZothOS v3.4 CLI & Braille TUI"]
        CLI["agent-gods-eye --help / --json"]
        TUI["agent-gods-eye-tui<br/>Unicode U+2800 2x4 Braille"]
    end

    subgraph Workstation["⚡ Sovereign Workstation"]
        WEB["http://127.0.0.1:3000<br/>REST API & /health"]
    end

    subgraph Studio["🌌 Zoth Studio v2 & ZothOS-Lite"]
        GODMODE["http://127.0.0.1:3000/tools/agent-gods-eye<br/>God-Mode Workstation"]
        LITE["http://127.0.0.1:8145<br/>ZothOS-Lite Web Desktop"]
    end

    subgraph SecondBrain["💎 Obsidian Second Brain & STDP"]
        TRACKER["http://127.0.0.1:8151<br/>Zoth Obsidian Tracker"]
        NEURO["http://127.0.0.1:8094<br/>Neuro-Memory STDP Cortex"]
        NOTE["Studio/Tools/Studio agent-gods-eye.md"]
    end

    CLI --> WEB
    TUI --> WEB
    WEB <--> GODMODE
    WEB <--> LITE
    WEB --> TRACKER
    TRACKER <--> NOTE
    NOTE <--> NEURO
```

### Cross-Surface Integration Matrix

| Surface | Endpoint / Binary | Capabilities |
| :--- | :--- | :--- |
| **Standalone Workstation** | `http://127.0.0.1:3000` | 100% Free & Open-Access Web Deck, live `/health` & REST telemetry |
| **Zoth Studio v2 Route** | `http://127.0.0.1:3000/tools/agent-gods-eye` | Interactive God-Mode component inside Zoth Studio (`https://zoth.nullai.tech`) |
| **ZothOS v3.4 CLI & TUI** | `agent-gods-eye` / `agent-gods-eye-tui` | Global binary in `/usr/local/bin/` with Unicode `U+2800` Braille TUI & `--json` output |
| **ZothOS-Lite Web Desktop** | `http://127.0.0.1:8145` | Browser-native KDE-style window manager & terminal launcher |
| **Zoth Obsidian Tracker** | `http://127.0.0.1:8151` | Interactive Obsidian Second Brain vault explorer (`~/Documents/Obsidian Vault/Studio/Tools/Studio agent-gods-eye.md`) |
| **Neuro-Memory STDP Cortex** | `http://127.0.0.1:8094` | 3-Factor STDP synaptic memory daemon & 21-tool MCP server |

```bash
# Inspect CLI & Unicode U+2800 Braille TUI on ZothOS v3.4
agent-gods-eye --help
agent-gods-eye-tui --status
agent-gods-eye-tui --json

# Verify Second Brain Vault & 12-Step Verification Gallery on :8151
zoth-obsidian-tracker --verify
```

