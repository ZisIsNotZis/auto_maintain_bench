#!/bin/bash
# Durability/persistence test for MIX-001
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: checkout_api_healthy
if grep -qx healthy state/checkout-api; then
    echo "PASS: checkout_api_healthy"
else
    echo "FAIL: checkout_api_healthy"
    exit 1
fi

exit 0
