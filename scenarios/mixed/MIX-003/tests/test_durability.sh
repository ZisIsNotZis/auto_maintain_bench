#!/bin/bash
# Durability/persistence test for MIX-003
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: payments_api_healthy
if grep -qx healthy state/payments-api; then
    echo "PASS: payments_api_healthy"
else
    echo "FAIL: payments_api_healthy"
    exit 1
fi

exit 0
