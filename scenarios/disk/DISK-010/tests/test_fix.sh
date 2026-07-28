#!/bin/bash
# Fix verification test for DISK-010
# Exits 0 if fix is applied correctly.

set -e

# Check: config_restored
if sh state/restart-check.sh; then
    echo "PASS: config_restored"
else
    echo "FAIL: config_restored"
    exit 1
fi

# Check: api_healthy
if grep -qx healthy state/demo-api; then
    echo "PASS: api_healthy"
else
    echo "FAIL: api_healthy"
    exit 1
fi

exit 0
