#!/bin/bash
# Durability/persistence test for HEALTH-007
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: repair_persisted
if grep -qx 'SYNC_ENABLED=true' etc/demo-api/sync.env; then
    echo "PASS: repair_persisted"
else
    echo "FAIL: repair_persisted"
    exit 1
fi

exit 0
