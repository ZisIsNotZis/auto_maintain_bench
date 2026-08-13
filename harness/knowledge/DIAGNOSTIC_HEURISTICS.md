# Diagnostic Heuristics

## How to Diagnose (Not Guess)

1. Start from the telemetry. Identify the exact error signal: service state, health status, stderr traceback, event severity, resource pressure.
2. Read the file at the line number the error points to. Do NOT guess the fix from the filename alone.
3. Trace the error backward: what causes this line to produce this error? Is it a config value? A missing dependency? A logic bug? An external condition?
4. Form a hypothesis: "If I change X to Y, the error should disappear because Z. This change will NOT break anything else because..."
5. **Check side effects**: Before applying the fix, think: does this change affect other parts of the system? Is Y a reasonable value, or does it create a new problem (e.g., setting a limit to 0 = unlimited, setting a timeout too high = hung connections)?
6. Test the hypothesis with one targeted edit. Verify. Restart.

## Symptom-to-Cause Map

### Service state = "failed" or "crashed"
- Read stderr lines for the specific error message
- Common causes (language-agnostic):
  - Config parse error: invalid YAML/TOML/JSON syntax, missing required key, wrong value type, trailing comma
  - Port/address conflict: another process on the same port, invalid bind address
  - Permission denied: can't read/write a file or directory, wrong ownership
  - Resource limit exceeded: file descriptor limit, memory limit, disk quota
  - Missing dependency: a required file, binary, library, or shared object not found
- Read the service's config file(s) — check the startup command or unit file to find where config lives
- Look for: typos, missing values, invalid formats, wrong types, path issues, unquoted special characters

### Health = "unhealthy" or "degraded"
- Health check failure is a SYMPTOM, not the root cause
- Find what the health check actually checks: a specific endpoint? a process? a file? a dependency? a database connection?
- The health check may be failing because: dependency is down, config timeout too short, the health endpoint itself has a bug, the check is too strict for normal operation, the health check is testing the wrong thing
- Do NOT just toggle a health mode flag or change the health check to always return OK — fix what the health check is actually testing

### High CPU usage
- Check notable_processes for the culprit
- Common causes: infinite loop, too many threads/workers, inefficient regex/parsing, compression at high level, polling with too-short interval, busy-waiting instead of event-driven, missing rate limiting
- Look for config keys like: WORKER_COUNT, THREAD_COUNT, POLL_INTERVAL_MS, COMPRESSION_LEVEL, MAX_CONCURRENCY, BATCH_SIZE
- The fix might be reducing a count, increasing an interval, or changing an algorithm setting

### High memory usage
- Check notable_processes for the culprit
- Common causes: unbounded cache growth, memory leak from accumulating data, loading entire dataset into memory, buffer that's too large, no garbage collection trigger, reference cycles preventing cleanup
- Look for config keys like: CACHE_SIZE, MAX_RESULTS, BUFFER_SIZE, CHUNK_SIZE, MAX_MEMORY_MB, GC_THRESHOLD
- If a cache has no limit configured, that's a common cause — growth without bound

### Disk space pressure
- Common causes: log files not rotated/compressed, temp files not cleaned up, database/journal files growing unbounded, stale backup files, core dumps, package caches
- Use `find` to locate large files/directories, then identify what config controls cleanup
- Look for config keys like: LOG_RETENTION_DAYS, MAX_LOG_SIZE, ROTATE_COUNT, TMP_CLEANUP_INTERVAL, MAX_BACKUP_COUNT

### Network errors / DNS failures
- Check connectivity fields in telemetry: dns_resolution_ok, default_route_ok, external_host_reachable
- Common causes: wrong nameserver address, timeout too short for slow network, IPv6 misconfiguration when IPv4 is expected, rate limiting on outbound connections, proxy misconfiguration, TLS certificate issues
- Check: resolv.conf, the service's network config, any proxy settings, firewall rules

### stderr contains traceback/stack trace
- Read the file and line number from the traceback — it tells you exactly what went wrong and where
- Language-specific patterns:
  - Python: ImportError, KeyError, ValueError, FileNotFoundError, AttributeError, SyntaxError, IndentationError, TypeError
  - Go: panic, nil pointer dereference, slice bounds out of range, index out of range
  - Node.js: TypeError, ReferenceError, ENOENT, EADDRINUSE, ECONNREFUSED, SyntaxError
  - Rust: panic, unwrap() on None/Err, index out of bounds
  - Java: NullPointerException, ArrayIndexOutOfBoundsException, ClassNotFoundException
  - Shell: command not found, permission denied, syntax error near unexpected token, unbound variable
  - Lua: attempt to index nil, attempt to call nil
  - Ruby: NoMethodError, NameError, Errno::ENOENT