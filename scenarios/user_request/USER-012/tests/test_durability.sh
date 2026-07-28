#!/bin/bash
# Durability/persistence test for USER-012
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: config_unchanged
if grep -qx 'CACHE_TTL=300' etc/web/performance.env; then
    echo "PASS: config_unchanged"
else
    echo "FAIL: config_unchanged"
    exit 1
fi

exit 0
