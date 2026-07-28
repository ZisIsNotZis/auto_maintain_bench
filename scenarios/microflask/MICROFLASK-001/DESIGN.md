# MICROFLASK-001 — Design Notes

## Overview

A realistic Python HTTP API service with two intentional code bugs:

1. **Connection leak in db.py**: `get_db()` creates a new sqlite3 connection on
   every call with no caching or close(). After ~32 requests, SQLite refuses
   further connections and the service fails health checks.

2. **Pagination off-by-one in handlers.py**: `offset = page * per_page` instead
   of `offset = (page - 1) * per_page`. The first page of results skips the
   first `per_page` items.

## Symptoms visible to agent

- Logs show `db connection failed: unable to open database file` after ~32 requests
- Logs show "restarting after health failure" cycle (restart_count=3)
- Memory trend rising (28% → 45%)
- First page of /items returns only items 11+, skipping items 1-10

## Fix (permanent)

- `db.py`: Add `conn.close()` after each query, or use `with sqlite3.connect(...) as conn:`
- `handlers.py`: Change `page * per_page` to `(page - 1) * per_page`

## Max score class

`fix_permanent` — both bugs are in editable Python source files.

## Why harder than existing scenarios

- Requires reading two Python files across modules
- Memory leak is not directly fixable by config — requires code patch
- Pagination bug requires understanding SQL query logic
- Both log and telemetry point to the same root cause (connection leak) but
  the pagination bug is a separate issue only visible via API probing
- Tests verify both source-level changes
