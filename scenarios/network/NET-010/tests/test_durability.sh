#!/bin/bash
# Durability/persistence test for NET-010
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: repair_persisted
if grep -qx 'PREFER_IPV6=false' etc/demo-api/network.env; then
    echo "PASS: repair_persisted"
else
    echo "FAIL: repair_persisted"
    exit 1
fi

exit 0
