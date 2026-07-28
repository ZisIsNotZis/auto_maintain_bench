#!/bin/bash
# Durability/persistence test for PROC-006
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: enablement_persisted
if grep -qx 'enabled' state/demo-api-enabled; then
    echo "PASS: enablement_persisted"
else
    echo "FAIL: enablement_persisted"
    exit 1
fi

exit 0
