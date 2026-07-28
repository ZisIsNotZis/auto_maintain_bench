#!/bin/bash
# Fix verification test for AGENT-007
# Exits 0 if fix is applied correctly.

set -e

# Check: typo_fixed
if grep -qx "ENABLE_GZIP=true" etc/logshipper/options.env; then
    echo "PASS: typo_fixed"
else
    echo "FAIL: typo_fixed"
    exit 1
fi

# Check: logshipper_healthy
if grep -qx healthy state/logshipper; then
    echo "PASS: logshipper_healthy"
else
    echo "FAIL: logshipper_healthy"
    exit 1
fi

exit 0
