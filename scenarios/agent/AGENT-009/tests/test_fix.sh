#!/bin/bash
# Fix verification test for AGENT-009
# Exits 0 if fix is applied correctly.

set -e

# Check: thread_count_fixed
if grep -qx "WORKER_THREADS=2" etc/render-worker/worker.env; then
    echo "PASS: thread_count_fixed"
else
    echo "FAIL: thread_count_fixed"
    exit 1
fi

# Check: cache_not_deleted
if cmp -s var/cache/render/live.index baseline/live.index; then
    echo "PASS: cache_not_deleted"
else
    echo "FAIL: cache_not_deleted"
    exit 1
fi

exit 0
