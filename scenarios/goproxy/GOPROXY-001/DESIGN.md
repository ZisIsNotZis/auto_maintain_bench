# GOPROXY-001 — Design Notes

## Overview

A realistic Go HTTP reverse proxy with a goroutine leak caused by unclosed
response bodies on error paths.

## Bug

Two body leak sites in `main.go`:

1. **ErrorHandler** (line ~30): When an upstream proxy request fails, the
   handler calls `http.Error(w, ...)` but never calls `r.Body.Close()`. The
   request body is leaked, keeping the underlying goroutine alive.

2. **ModifyResponse** (line ~40): When upstream returns 404, the function
   returns `io.EOF` but never calls `resp.Body.Close()`. The transport layer
   leaks the connection body on error return.

Combined, these cause goroutine count to grow from ~8 to 100+ under
sustained load, leading to OOM kills and service restart loops.

## Symptoms visible to agent

- Logs show `goroutine count` warnings growing from 48 → 67 → 89 → 112
- `CRITICAL: goroutine count=112, memory=248MB, possible leak`
- Service restart count: 4 in 30 minutes
- Memory trend: 18% → 42% before OOM
- Proxy state: "degraded", service health: "unhealthy"

## Fix (permanent)

Add missing `Body.Close()` calls:

- In `ErrorHandler`: add `r.Body.Close()` before the HTTP error response
- In `ModifyResponse`: add `resp.Body.Close()` before returning `io.EOF`
- Rebuild: `cd /sandbox && go build -o goproxy-server .`
- Update state: `echo "ok" > /sandbox/var/state/proxy_status`

The Go compiler (golang) is available in the sandbox Docker image.

## Max score class

`fix_permanent` — requires source code change and recompilation.

## Why harder than existing scenarios

- Requires understanding Go http.Handler interface and reverse proxy lifecycle
- Bug manifests as OOM/restart loop but root cause is in two different
  callback functions (ErrorHandler and ModifyResponse)
- Fix requires recompilation with Go toolchain (not just config edit)
- Goroutine leak pattern is subtle — symptoms don't directly name "body close"
- Multiple interacting components: request routing, error handling, response
  modification
