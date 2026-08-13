# Config File Patterns

## Where Config Files Live

Config files can be anywhere. Common locations (but NOT exhaustive):
- `etc/<service>/` — service-specific config directory
- `config/` — application config directory
- `.env` or `.env.production` — root-level environment file
- `config.yaml`, `config.yml`, `config.toml`, `config.json` — root-level config
- `.config/`, `.conf/` — hidden config directories
- `<service>.conf`, `<service>.ini`, `<service>.cfg` — named config files
- `appsettings.json`, `settings.py`, `application.properties` — framework-specific
- `Cargo.toml`, `package.json`, `go.mod` — language-specific project configs (may contain runtime settings)

**How to find the actual config**: Read the README, check the service's startup command (`systemctl cat <service>` or check the unit file), search for common extensions.

## Common Config Formats

### Key-Value / Environment files (.env, .conf, .ini)
```
KEY=value
OTHER_KEY=other_value
# This is a comment
; This is also a comment (INI style)
```
- One KEY=VALUE per line
- Blank lines and comment lines are ignored
- Values may or may not be quoted
- Some formats support sections: `[section]\nkey=value`
- Watch for: spaces around `=`, unquoted values with special characters

### YAML (.yaml, .yml)
```
server:
  port: 8080
  host: 0.0.0.0
  timeout: 30s
cache:
  enabled: true
  max_size: 256
```
- Indentation matters (usually 2 or 4 spaces)
- Keys and values separated by `: `
- Lists use `- item` prefix
- Values can be: strings, numbers, booleans, durations, lists, nested objects
- Common issues: wrong indentation, missing space after colon, tabs vs spaces

### TOML (.toml)
```
[server]
port = 8080
host = "0.0.0.0"
timeout = "30s"

[cache]
enabled = true
max_size = 256
```
- Sections in `[brackets]`
- `key = value` format
- Values: strings (quoted), numbers, booleans, arrays, nested tables
- Common issues: missing section header, wrong value type

### JSON (.json)
```
{
  "server": {
    "port": 8080,
    "host": "0.0.0.0",
    "timeout": "30s"
  }
}
```
- Strict syntax: double quotes, no trailing commas, braces/brackets must match
- Common issues: trailing comma after last item, single quotes, missing comma

### Config Files in Code
Some apps define config in source code files:
- Python: `settings.py`, `config.py` — variables and dictionaries
- JavaScript/TypeScript: `config.js`, `config.ts` — exported objects
- Go: often uses flags, env vars, or external config files; sometimes `config.go`
- Rust: often uses TOML or environment variables; sometimes `config.rs`
- Java: `.properties` files, `application.yml`, or XML configs

## Common Config Keys and What They Mean

### Resource Limits
- Keys like `MAX_*`, `*_LIMIT`, `*_CAP`, `*_QUOTA`, `*_THRESHOLD` often control limits
- Setting to 0 or -1 may mean "unlimited" or "disabled" — check the context and documentation
- Too high a limit → resource exhaustion. Too low → service can't function.

### Timeouts
- Keys like `*_TIMEOUT`, `*_DEADLINE`, `*_TTL`, `*_INTERVAL`, `*_DELAY`
- Usually in milliseconds, seconds, or a duration string like "30s", "5m", "1h"
- Too short → spurious failures under load. Too long → resource leaks, hung connections.

### Concurrency
- Keys like `*_THREADS`, `*_WORKERS`, `*_POOL_SIZE`, `*_CONCURRENCY`, `*_PARALLEL`
- Too many → CPU/memory overuse, context switching overhead. Too few → request queue buildup.

### Retry / Backoff
- Keys like `*_RETRY`, `*_BACKOFF`, `*_ATTEMPTS`, `*_RETRIES`
- Too aggressive retry → thundering herd, resource waste. Too timid → prolonged outages.

### Logging
- Keys like `LOG_LEVEL`, `LOG_FILE`, `LOG_FORMAT`, `*_ROTATION`
- Log levels: debug, info, warn/warning, error, critical/fatal
- Too verbose logging → disk fill. Too quiet → can't debug.
- `debug` or `trace` level logs are usually too verbose for production

### Caching
- Keys like `*_CACHE`, `*_TTL`, `*_EXPIRE`, `*_EVICT`
- No cache limit → unbounded growth. Too short TTL → cache misses, performance degradation.
- Too aggressive caching → stale data, memory pressure.

## How to Read Config Files

1. Always `cat` the file before editing — know the exact current state
2. Look for the specific key mentioned in the error message
3. Check if the value makes sense in context (e.g., 0 often means "unlimited" or "disabled")
4. Compare with expected behavior: if the service is using too much memory, look for limits that are too high or set to 0/unlimited
5. Check for syntax errors in the file: trailing commas, missing quotes, wrong indentation
6. If the config references other files (imports, includes), check those too