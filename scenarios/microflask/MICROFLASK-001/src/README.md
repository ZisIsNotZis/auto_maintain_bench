# MicroFlask API

MicroFlask is a lightweight Python HTTP API service for managing
catalog items. It uses SQLite for storage and runs as a systemd unit.

## Quick Start

```bash
cd /path/to/microflask
./start.sh
```

The service listens on `http://localhost:8080` and exposes:

- `GET /health` — service health
- `GET /items?page=N&per_page=M` — list items with pagination
- `POST /items` — create a new item (JSON body: `{"name": "...", "price": N}`)
- `GET /items/<id>` — get single item

## Configuration

See `config.env` for tunable parameters:

- `HOST`: bind address (default: 127.0.0.1)
- `PORT`: listen port (default: 8080)
- `DB_PATH`: SQLite database path
- `MAX_CONNECTIONS`: max open connections (default: 32)
- `LOG_LEVEL`: logging verbosity (default: INFO)

## Health

The `/health` endpoint checks database connectivity.
If the database is unreachable, the service returns 503.

## Operations

- Health check: `./health.sh`
- Restart: `systemctl restart microflask`
- Logs: `tail -f var/log/app.log`

The service opens a new database connection for each request. Under sustained
traffic the connection limit is reached and further requests are refused
until existing connections are released.
