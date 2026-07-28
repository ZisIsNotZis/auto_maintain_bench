#!/bin/bash
# Durability/persistence test for CPU-008
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: thread_pool_persisted
if value=$(sed -n 's/^THREAD_POOL_SIZE=//p' etc/demo-api/threadpool.env); [ -n "$value" ] && [ "$value" -ge 4 ]; then
    echo "PASS: thread_pool_persisted"
else
    echo "FAIL: thread_pool_persisted"
    exit 1
fi

exit 0
