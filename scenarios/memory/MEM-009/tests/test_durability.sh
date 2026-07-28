#!/bin/bash
# Durability/persistence test for MEM-009
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: fragmentation_guard_persisted
if arena=$(sed -n 's/^MALLOC_ARENA_MAX=//p' etc/demo-api/malloc.env); maxreq=$(sed -n 's/^WORKER_MAX_REQUESTS=//p' etc/demo-api/malloc.env); [ -n "$arena" ] && [ -n "$maxreq" ] && [ "$arena" -le 2 ] && [ "$maxreq" -ge 1000 ]; then
    echo "PASS: fragmentation_guard_persisted"
else
    echo "FAIL: fragmentation_guard_persisted"
    exit 1
fi

exit 0
