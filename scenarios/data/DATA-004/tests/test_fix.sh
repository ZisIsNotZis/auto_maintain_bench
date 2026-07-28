#!/bin/bash
# Fix verification test for DATA-004
# Exits 0 if fix is applied correctly.

set -e

# Check: lock_removed
if test ! -e var/db/orders.db.lock; then
    echo "PASS: lock_removed"
else
    echo "FAIL: lock_removed"
    exit 1
fi

# Check: api_healthy
if grep -qx healthy state/orders-api; then
    echo "PASS: api_healthy"
else
    echo "FAIL: api_healthy"
    exit 1
fi

exit 0
