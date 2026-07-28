#!/bin/bash
# Durability/persistence test for MEM-006
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: tmpfs_limit_persisted
if limit=$(sed -n 's/^TMPFS_CACHE_LIMIT_MB=//p' etc/demo-api/tmpfs.env); [ -n "$limit" ] && [ "$limit" -ge 16 ] && [ "$limit" -le 64 ]; then
    echo "PASS: tmpfs_limit_persisted"
else
    echo "FAIL: tmpfs_limit_persisted"
    exit 1
fi

exit 0
