#!/bin/bash
# Durability/persistence test for HEALTH-005
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: repair_persisted
if grep -qx 'POOL_TIMEOUT_MS=5000' etc/demo-api/db.env; then
    echo "PASS: repair_persisted"
else
    echo "FAIL: repair_persisted"
    exit 1
fi

exit 0
