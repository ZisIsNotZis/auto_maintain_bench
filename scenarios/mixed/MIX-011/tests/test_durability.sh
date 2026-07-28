#!/bin/bash
# Durability/persistence test for MIX-011
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: exporter_stays_healthy
if grep -qx healthy state/exporter; then
    echo "PASS: exporter_stays_healthy"
else
    echo "FAIL: exporter_stays_healthy"
    exit 1
fi

exit 0
