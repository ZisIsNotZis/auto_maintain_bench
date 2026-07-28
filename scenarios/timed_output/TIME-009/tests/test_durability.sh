#!/bin/bash
# Durability/persistence test for TIME-009
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: slow_app_healthy
if grep -qx healthy state/slow-app; then
    echo "PASS: slow_app_healthy"
else
    echo "FAIL: slow_app_healthy"
    exit 1
fi

exit 0
