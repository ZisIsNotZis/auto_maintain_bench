#!/bin/bash
# Fix verification test for DATA-003
# Exits 0 if fix is applied correctly.

set -e

# Check: index_restored
if grep -qx 'orders,customer_id' var/db/analytics.indexes; then
    echo "PASS: index_restored"
else
    echo "FAIL: index_restored"
    exit 1
fi

# Check: api_healthy
if grep -qx healthy state/analytics-api; then
    echo "PASS: api_healthy"
else
    echo "FAIL: api_healthy"
    exit 1
fi

exit 0
