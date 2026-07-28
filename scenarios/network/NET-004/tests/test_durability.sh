#!/bin/bash
# Durability/persistence test for NET-004
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: repair_persisted
if grep -qx 'NOT_AFTER=2027-01-01T00:00:00Z' etc/demo-api/upstream-cert.env; then
    echo "PASS: repair_persisted"
else
    echo "FAIL: repair_persisted"
    exit 1
fi

exit 0
