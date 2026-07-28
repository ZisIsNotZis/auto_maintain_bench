#!/bin/bash
# Durability/persistence test for MIX-002
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: backoff_persisted
if grep -qx "RETRY_BACKOFF_MS=250" etc/order-api/retry.env; then
    echo "PASS: backoff_persisted"
else
    echo "FAIL: backoff_persisted"
    exit 1
fi

exit 0
