#!/bin/bash
# Fix verification test for CPU-007
# Exits 0 if fix is applied correctly.

set -e

# Check: cpu_below_threshold
if sh state/restart-check.sh; then
    echo "PASS: cpu_below_threshold"
else
    echo "FAIL: cpu_below_threshold"
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
