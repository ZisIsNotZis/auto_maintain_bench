#!/bin/bash
# Durability/persistence test for HEALTH-006
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: repair_persisted
if grep -qx 'WORKER_CONCURRENCY=4' etc/demo-api/worker.env; then
    echo "PASS: repair_persisted"
else
    echo "FAIL: repair_persisted"
    exit 1
fi

exit 0
