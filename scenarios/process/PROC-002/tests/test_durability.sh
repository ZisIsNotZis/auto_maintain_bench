#!/bin/bash
# Durability/persistence test for PROC-002
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: repair_persisted
if grep -qx 'BOOTSTRAP_OK=true' etc/demo-api/bootstrap.env; then
    echo "PASS: repair_persisted"
else
    echo "FAIL: repair_persisted"
    exit 1
fi

exit 0
