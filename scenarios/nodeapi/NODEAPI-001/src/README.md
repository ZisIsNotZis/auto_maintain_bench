# NodeAPI — REST Item Service

NodeAPI is a Node.js REST API for managing catalog items. It uses a file-based
JSON store and runs as a systemd unit.

## Quick Start

```bash
cd /path/to/nodeapi
./start.sh
```

The service listens on `http://localhost:8080`.

## Endpoints

- `GET /health` — service health
- `GET /items?page=1&limit=10` — list items with pagination
- `POST /items` — create a new item (JSON: `{"name": "...", "price": N}`)
- `GET /status` — process stats

## Configuration

Environment variables:

- `PORT`: listen port (default: 8080)
- `AUTH_TOKEN`: bearer token for admin access (default: dev-token-1234)
- `DATA_DIR`: items data directory

## Operations

- Start: `./start.sh`
- Health: `curl http://localhost:8080/health`
- Restart: `kill $(cat /sandbox/var/run/nodeapi.pid) && ./start.sh`
- Logs: `tail -f /sandbox/var/log/api.log`
