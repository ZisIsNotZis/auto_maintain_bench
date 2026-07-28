#!/bin/bash
# Fix verification test for PROC-009
# Exits 0 if fix is applied correctly.

set -e

# Check: lock_removed
if [ ! -e var/lock/demo-api.pid.lock ]; then
    echo "PASS: lock_removed"
else
    echo "FAIL: lock_removed"
    exit 1
fi

# Check: api_healthy
if grep -qx healthy state/demo-api; then
    echo "PASS: api_healthy"
else
    echo "FAIL: api_healthy"
    exit 1
fi

exit 0
