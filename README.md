# Agent God's Eye

Shodan OSINT radar: run Shodan queries, normalise the results into targets, and plot them on a 3D globe in a local web deck. Standard library only.

## Usage

```bash
./bin/agent-gods-eye search "port:554 has_screenshot:true" --limit 20   # one-off scan
./bin/agent-gods-eye serve --port 8112                                  # web deck + REST API
./bin/agent-gods-eye status                                             # check the daemon
```

### Shodan key
Read from `SHODAN_API_KEY` (or `SHODAN_API`), then `~/.config/shodan/.env`. `--key` works but is visible in `ps` and shell history. Without a key the tool runs in offline community mode.

## REST API (default http://127.0.0.1:8112)

| Endpoint | Purpose |
|---|---|
| `GET /api/info` | Shodan plan / credits |
| `POST /api/search` | Run a query |
| `GET /api/targets`, `/api/stats` | Stored results |
| `GET /api/host/<ip>` | Host detail |
| `GET /api/stream` | Live SSE events |
| `GET /api/export` | Export results |

## Security
- Binds to `127.0.0.1` by default; override with `--host` / `ZOTH_BIND_HOST` only on trusted networks.
- CORS echoes only local origins; cross-origin POSTs get 403 (stops other websites spending your Shodan credits).
- Static file serving rejects `../` traversal.
- Only scan infrastructure you are authorised to assess; respect Shodan's terms.

## Tests
```bash
python3 -m pytest -q tests
```
