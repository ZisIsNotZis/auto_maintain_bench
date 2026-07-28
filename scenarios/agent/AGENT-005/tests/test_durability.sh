#!/bin/bash
# Durability/persistence test for AGENT-005
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: worker_healthy
if grep -qx healthy state/cache-worker; then
    echo "PASS: worker_healthy"
else
    echo "FAIL: worker_healthy"
    exit 1
fi

exit 0
