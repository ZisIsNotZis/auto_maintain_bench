#!/bin/bash
# Durability/persistence test for MIX-005
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: worker_back_healthy
if grep -qx healthy state/cache-worker; then
    echo "PASS: worker_back_healthy"
else
    echo "FAIL: worker_back_healthy"
    exit 1
fi

exit 0
