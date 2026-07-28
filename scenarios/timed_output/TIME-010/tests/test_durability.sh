#!/bin/bash
# Durability/persistence test for TIME-010
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: worker_stays_healthy
if grep -qx healthy state/flaky-worker; then
    echo "PASS: worker_stays_healthy"
else
    echo "FAIL: worker_stays_healthy"
    exit 1
fi

exit 0
