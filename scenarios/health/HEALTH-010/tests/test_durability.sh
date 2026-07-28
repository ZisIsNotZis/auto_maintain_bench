#!/bin/bash
# Durability/persistence test for HEALTH-010
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: mitigation_persisted
if grep -qx 'ALLOW_PARTIAL_RESULTS=true' etc/demo-api/degraded-mode.env; then
    echo "PASS: mitigation_persisted"
else
    echo "FAIL: mitigation_persisted"
    exit 1
fi

exit 0
