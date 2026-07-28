#!/bin/bash
# Durability/persistence test for MEM-001
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: cache_limit_persisted
if limit=$(sed -n 's/^CACHE_LIMIT_MB=//p' etc/demo-api/cache.env); [ -n "$limit" ] && [ "$limit" -ge 64 ] && [ "$limit" -le 256 ]; then
    echo "PASS: cache_limit_persisted"
else
    echo "FAIL: cache_limit_persisted"
    exit 1
fi

exit 0
