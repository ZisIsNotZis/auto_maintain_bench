#!/bin/bash
# Durability/persistence test for SEC-010
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: world_writable_temp_removed
if ! grep -q "chmod 666" app/export.sh && grep -qx secure state/report-exporter; then
    echo "PASS: world_writable_temp_removed"
else
    echo "FAIL: world_writable_temp_removed"
    exit 1
fi

exit 0
