# Telemetry Design

## Principles

1. **Everything a maintainer needs on wakeup** — Every signal needed to assess host health
   must be in the telemetry JSON. No require to look at separate files.
2. **Trend/curve data** — Where history matters, use `{timestamp: value}` maps
   `(e.g. usage_pct_trend)`. For compact arrays, encode interval in the field name
   `(e.g. usage_pct_every10s: [72, 91, 99])`.
3. **Layered visibility** — The telemetry highlight extractor surfaces actionable
   signals first; the full JSON dump provides all raw data.
4. **Stdout + Stderr** — Every service has both stdout and stderr. Stdout captures
   operator requests, startup messages, and routine status. Stderr captures errors,
   warnings, and diagnostic output.

## Host-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `observed_at` | ISO-8601 | Telemetry collection timestamp |
| `uptime_s` | int | Host uptime in seconds |
| `cpu.logical_cores` | int | Number of logical CPU cores |
| `cpu.usage_pct` | float | Current CPU utilization (0-100) |
| `cpu.usage_pct_trend` | `{timestamp: value}` | CPU utilization over recent samples |
| `cpu.load_1m` | float | 1-minute load average |
| `cpu.load_5m` | float | 5-minute load average |
| `cpu.load_15m` | float | 15-minute load average |
| `cpu.pressure_some_pct` | float | PSI "some" pressure (0-100) |
| `cpu.throttled` | bool | Whether CPU is throttled |
| `memory.total_bytes` | int | Total physical RAM (bytes) |
| `memory.available_bytes` | int | Available RAM (bytes) |
| `memory.used_pct` | float | Memory usage percentage (0-100) |
| `memory.used_pct_trend` | `{timestamp: value}` | Memory usage over recent samples |
| `memory.swap_total_bytes` | int | Total swap space (bytes) |
| `memory.swap_used_bytes` | int | Used swap space (bytes) |
| `memory.pressure_some_pct` | float | Memory PSI "some" pressure |
| `memory.oom_kills_since_boot` | int | OOM killer invocations |
| `filesystems[].mount` | str | Mount point path |
| `filesystems[].fs_type` | str | Filesystem type (ext4, overlay, tmpfs) |
| `filesystems[].total_bytes` | int | Total filesystem size |
| `filesystems[].free_bytes` | int | Free space |
| `filesystems[].used_pct` | float | Space usage percentage |
| `filesystems[].used_pct_trend` | `{timestamp: value}` | Space usage over recent samples |
| `filesystems[].inode_used_pct` | float | Inode usage percentage |
| `filesystems[].read_only` | bool | Whether mounted read-only |
| `filesystems[].io_errors_since_boot` | int | Cumulative I/O errors |
| `network_interfaces[].name` | str | Interface name (eth0, lo) |
| `network_interfaces[].state` | str | Interface state (up/down) |
| `network_interfaces[].carrier` | bool | Carrier signal detected |
| `network_interfaces[].loopback` | bool | Whether loopback interface |
| `network_interfaces[].default_route` | bool | Whether this is the default route interface |
| `network_interfaces[].mtu` | int | MTU value |
| `network_interfaces[].speed_mbps` | int | Link speed (optional) |
| `network_interfaces[].rx_bytes_s` | int | Receive throughput |
| `network_interfaces[].tx_bytes_s` | int | Transmit throughput |
| `network_interfaces[].rx_errors_s` | int | Receive errors |
| `network_interfaces[].tx_errors_s` | int | Transmit errors |
| `network_interfaces[].rx_drops_s` | int | Receive drops |
| `network_interfaces[].tx_drops_s` | int | Transmit drops |
| `connectivity.default_route_ok` | bool | Whether the default route is reachable |
| `connectivity.dns_resolution_ok` | bool | Whether DNS resolution works |
| `notable_processes[]` | array | Outlier processes (details below) |
| `host_events[]` | array | Host-level events (details below) |
| `services[]` | array | Managed services (detailed below) |
| `escalating[]` | array | Escalated issues from prior cycles |
| `collection_errors[]` | array | Telemetry collection failures |

### Notable Process

| Field | Type | Description |
|-------|------|-------------|
| `pid` | int | Process ID |
| `ppid` | int | Parent process ID |
| `name` | str | Process name |
| `state` | str | Process state (running, sleeping, zombie, etc.) |
| `cpu_pct` | float | CPU usage percentage |
| `memory_bytes` | int | Resident memory in bytes |
| `age_s` | int | Process age in seconds |
| `reasons` | [str] | Why this process is notable (high_memory, high_cpu, zombie) |
| `cmdline` | str | Full command line |

### Host Event

| Field | Type | Description |
|-------|------|-------------|
| `severity` | str | One of: critical, error, warning, info |
| `kind` | str | Event category (resource, security, network, health, filesystem, configuration) |
| `code` | str | Machine-readable event code |
| `message` | str | Human-readable description |
| `count` | int | How many times this event fired |
| `first_seen_at` | ISO-8601 | First occurrence |
| `last_seen_at` | ISO-8601 | Most recent occurrence |

## Service Fields

Each service in the `services[]` array:

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Service name |
| `manager` | str | Process manager (systemd, supervisord, etc.) |
| `enabled` | bool | Whether service starts on boot |
| `state` | str | Runtime state (running, failed, stopped, starting) |
| `health` | str | Application health (healthy, degraded, unhealthy) |
| `main_pid` | int | Main process PID |
| `uptime_s` | int | Seconds since service last started |
| `restart_count` | int | Number of restarts since boot |
| `cpu_pct` | float | Service CPU utilization (0-100) |
| `cpu_pct_trend` | `{timestamp: value}` | CPU over recent samples |
| `memory_bytes` | int | Service resident memory |
| `memory_pct` | float | Service memory as % of total RAM |
| `threads` | int | Thread count |
| `fd_open` | int | Open file descriptors |
| `fd_limit` | int | File descriptor limit |
| `stdout.new_line_count` | int | New stdout lines since last collection |
| `stdout.lines` | [str] | Recent stdout output lines |
| `stderr.new_line_count` | int | New stderr lines since last collection |
| `stderr.lines` | [str] | Recent stderr output lines |
| `events[]` | array | Service-level events (same format as host events) |
| `last_output_at` | ISO-8601 | Timestamp of most recent stdout or stderr line |
| `requests` (optional) | object | Request metrics for request-serving services |
| `requests.rate_s` | float | Request rate per second |
| `requests.error_pct` | float | Error percentage |
| `requests.error_pct_trend` | `{timestamp: value}` | Error rate trend |
| `requests.latency_p50_ms` | float | P50 latency in milliseconds |
| `requests.latency_p95_ms` | float | P95 latency |
| `requests.latency_p99_ms` | float | P99 latency |
| `requests.inflight` | int | Currently in-flight requests |
| `queue` (optional) | object | Queue metrics for queued services |
| `queue.depth` | int | Current queue depth |
| `queue.depth_trend` | `{timestamp: value}` | Queue depth trend |
| `queue.oldest_age_s` | int | Age of oldest queued item |

## Service Log Conventions

**stdout** contains:
- Operator requests ("approved operator request: ...")
- Startup/initialization messages ("Starting with CONFIG=...")
- Routine operational output ("request completed in 42ms")
- Status updates ("cache flush completed")

**stderr** contains:
- Errors and exceptions ("write failed: ENOSPC")
- Warnings ("scheduler latency exceeded 1800ms")
- Diagnostics pointing to config files ("loaded KEY=VALUE from /sandbox/etc/...")
- Tracebacks and crash information

## Trend Data Format

Two accepted formats:

### Explicit timestamps (preferred for low-frequency data)
```json
"usage_pct_trend": {
  "2026-07-22T07:29:40Z": 72,
  "2026-07-22T07:29:50Z": 91,
  "2026-07-22T07:30:00Z": 99
}
```

### Compact array with interval in name (for high-frequency data)
```json
"usage_pct_every10s": [72, 91, 99],
"depth_every30s": [280, 560, 840]
```

The `_everyNs` suffix encodes the interval between samples. The most recent
sample is last. The field name must include `_every` followed by a positive
integer followed by `s` for seconds.

## Highlight Extraction

The `_extract_telemetry_highlights()` method in `maintenance_loop.py` produces
a compact plain-text summary for every telemetry snapshot:

1. **Unhealthy services** — state != "running" or health != "healthy"
2. **Stdout lines** — from unhealthy services or requests
3. **Stderr lines** — from all services
4. **Critical/error events** — service and host level
5. **Request error rates** — when >10%
6. **Resource alerts** — CPU >80%, memory >80%, filesystem >90%
7. **Connectivity failures** — DNS or default route
8. **Notable processes** — all entries
9. **Escalating issues** — all entries
10. **Restart counts** — services with restart_count > 0

## Validation (contracts.py)

Every telemetry snapshot is validated by `validate_telemetry()`:
- `observed_at` must be a non-empty ISO-8601 string
- `cpu`, `memory` must have required fields with trends
- `filesystems[]` must have `used_pct` with `used_pct_trend`
- `network_interfaces[]` must have rx/tx throughput
- `services[]` must have `cpu_pct` and `memory_bytes` with trends
- `services[].events` with `severity`, `kind`, `code`, `message`
- `stdout` and `stderr` if present must have `new_line_count` and `lines`
- `last_output_at` if present must be ISO-8601
