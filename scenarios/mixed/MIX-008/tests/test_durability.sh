#!/bin/bash
# Durability/persistence test for MIX-008
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: proxy_healthy
if grep -qx healthy state/queue-proxy && grep -qx yes state/drained; then
    echo "PASS: proxy_healthy"
else
    echo "FAIL: proxy_healthy"
    exit 1
fi

exit 0
