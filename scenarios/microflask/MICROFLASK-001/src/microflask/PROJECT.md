# MicroFlask API

MicroFlask is a lightweight Python HTTP API service for managing
catalog items. It uses SQLite for storage and runs as a systemd unit.

## Quick Start

```bash
./start.sh
```

The service listens on `http://localhost:8080` and exposes:

- `GET /health` — service health
- `GET /items?page=N&per_page=M` — list items with pagination
- `POST /items` — create a new item (JSON body: `{"name": "...", "price": N}`)
- `GET /items/<id>` — get single item

## Configuration

See `config.env` for tunable parameters.

## Operations

- Health: `./health.sh`
- Restart: `systemctl restart microflask`
- Logs: `tail -f var/log/app.log`

The service opens a database connection for each request. This is normal
for the expected low-traffic deployment. If traffic grows significantly,
consider adding connection pooling.
