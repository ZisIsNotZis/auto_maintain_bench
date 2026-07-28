#!/bin/bash
# Durability/persistence test for MIX-007
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: alerts_api_healthy
if grep -qx healthy state/alerts-api; then
    echo "PASS: alerts_api_healthy"
else
    echo "FAIL: alerts_api_healthy"
    exit 1
fi

exit 0
