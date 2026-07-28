#!/bin/bash
# Fix verification test for MIX-002
# Exits 0 if fix is applied correctly.

set -e

# Check: retry_backoff_set
if grep -qx "RETRY_BACKOFF_MS=250" etc/order-api/retry.env; then
    echo "PASS: retry_backoff_set"
else
    echo "FAIL: retry_backoff_set"
    exit 1
fi

# Check: order_api_healthy
if grep -qx healthy state/order-api; then
    echo "PASS: order_api_healthy"
else
    echo "FAIL: order_api_healthy"
    exit 1
fi

exit 0
