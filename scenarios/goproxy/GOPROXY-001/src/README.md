# GoProxy — HTTP Reverse Proxy

GoProxy is a lightweight HTTP reverse proxy written in Go. It forwards incoming
requests to an upstream backend service and handles authentication header
forwarding.

## Architecture

```
Client → GoProxy (:8080) → Backend (:9000)
```

## Quick Start

```bash
cd /path/to/goproxy
./start.sh
```

The proxy listens on port 8080 and forwards to `http://backend:9000`.

## Endpoints

- `GET /health` — proxy health check
- `GET /config` — proxy configuration dump
- `GET /api/*` — proxied to backend service
- `POST /api/*` — proxied to backend service

## Configuration

The upstream target is hardcoded in `main.go`. On startup, the proxy writes
its PID to `/sandbox/var/run/goproxy.pid` and logs to `/sandbox/var/log/proxy.log`.

## Health

```bash
./health.sh
```

Returns 0 if the proxy process is running, 1 otherwise.

## Operations

- Health check: `./health.sh`
- Restart: `kill $(cat /sandbox/var/run/goproxy.pid) && ./start.sh`
- Logs: `cat /sandbox/var/log/proxy.log`

## Known Issues

Under sustained traffic the proxy's memory and goroutine count grows
monotonically. Periodically the process is OOM-killed by the kernel and
must be restarted by the watchdog.
