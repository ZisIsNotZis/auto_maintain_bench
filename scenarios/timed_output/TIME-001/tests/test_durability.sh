#!/bin/bash
# Durability/persistence test for TIME-001
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: worker_healthy
if grep -qx healthy state/worker; then
    echo "PASS: worker_healthy"
else
    echo "FAIL: worker_healthy"
    exit 1
fi

exit 0
