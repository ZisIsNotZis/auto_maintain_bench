#!/bin/bash
# Durability/persistence test for AGENT-006
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: cache_healthy
if grep -qx healthy state/thumb-cache; then
    echo "PASS: cache_healthy"
else
    echo "FAIL: cache_healthy"
    exit 1
fi

exit 0
