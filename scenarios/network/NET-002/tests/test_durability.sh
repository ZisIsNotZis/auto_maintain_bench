#!/bin/bash
# Durability/persistence test for NET-002
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: backoff_persisted
if grep -qx 'BACKOFF_MS=2000' etc/demo-api/client.env; then
    echo "PASS: backoff_persisted"
else
    echo "FAIL: backoff_persisted"
    exit 1
fi

exit 0
