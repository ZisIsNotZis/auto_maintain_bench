#!/bin/bash
# Durability/persistence test for NET-005
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: repair_persisted
if grep -qx 'CLIENT_TIME_OFFSET_S=0' etc/demo-api/client-time.env; then
    echo "PASS: repair_persisted"
else
    echo "FAIL: repair_persisted"
    exit 1
fi

exit 0
