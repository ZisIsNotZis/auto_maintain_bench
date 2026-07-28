#!/bin/bash
# Fix verification test for HEALTH-010
# Exits 0 if fix is applied correctly.

set -e

# Check: partial_results_enabled
if grep -qx 'ALLOW_PARTIAL_RESULTS=true' etc/demo-api/degraded-mode.env; then
    echo "PASS: partial_results_enabled"
else
    echo "FAIL: partial_results_enabled"
    exit 1
fi

# Check: dependency_recovered
if grep -qx healthy state/demo-api; then
    echo "PASS: dependency_recovered"
else
    echo "FAIL: dependency_recovered"
    exit 1
fi

exit 0
