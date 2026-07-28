#!/bin/bash
# Durability/persistence test for CPU-005
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: retry_backoff_persisted
if value=$(sed -n 's/^RETRY_BACKOFF_MS=//p' etc/demo-api/retry.env); [ -n "$value" ] && [ "$value" -ge 200 ]; then
    echo "PASS: retry_backoff_persisted"
else
    echo "FAIL: retry_backoff_persisted"
    exit 1
fi

exit 0
