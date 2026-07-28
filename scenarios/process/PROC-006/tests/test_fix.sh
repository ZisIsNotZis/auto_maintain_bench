#!/bin/bash
# Fix verification test for PROC-006
# Exits 0 if fix is applied correctly.

set -e

# Check: service_enabled
if grep -qx 'enabled' state/demo-api-enabled; then
    echo "PASS: service_enabled"
else
    echo "FAIL: service_enabled"
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
