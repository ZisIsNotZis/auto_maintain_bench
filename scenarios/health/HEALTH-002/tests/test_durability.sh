#!/bin/bash
# Durability/persistence test for HEALTH-002
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: repair_persisted
if grep -qx 'READINESS_GATE=queue_depth' etc/demo-api/health.env; then
    echo "PASS: repair_persisted"
else
    echo "FAIL: repair_persisted"
    exit 1
fi

exit 0
