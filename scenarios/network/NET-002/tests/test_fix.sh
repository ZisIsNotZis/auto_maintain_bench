#!/bin/bash
# Fix verification test for NET-002
# Exits 0 if fix is applied correctly.

set -e

# Check: backoff_enabled
if grep -qx 'BACKOFF_MS=2000' etc/demo-api/client.env; then
    echo "PASS: backoff_enabled"
else
    echo "FAIL: backoff_enabled"
    exit 1
fi

# Check: upstream_recovered
if grep -qx healthy state/demo-api; then
    echo "PASS: upstream_recovered"
else
    echo "FAIL: upstream_recovered"
    exit 1
fi

exit 0
