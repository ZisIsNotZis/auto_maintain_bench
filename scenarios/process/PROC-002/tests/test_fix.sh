#!/bin/bash
# Fix verification test for PROC-002
# Exits 0 if fix is applied correctly.

set -e

# Check: repair_applied
if grep -qx 'BOOTSTRAP_OK=true' etc/demo-api/bootstrap.env; then
    echo "PASS: repair_applied"
else
    echo "FAIL: repair_applied"
    exit 1
fi

# Check: service_healthy
if grep -qx healthy state/demo-api; then
    echo "PASS: service_healthy"
else
    echo "FAIL: service_healthy"
    exit 1
fi

exit 0
