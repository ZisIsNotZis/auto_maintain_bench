#!/bin/bash
# Durability/persistence test for PROC-005
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: repair_persisted
if grep -qx 'SPAWN_PER_REQUEST=false' etc/demo-api/fork.env; then
    echo "PASS: repair_persisted"
else
    echo "FAIL: repair_persisted"
    exit 1
fi

exit 0
