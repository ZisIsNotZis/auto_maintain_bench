#!/bin/bash
# Fix verification test for USER-008
# Exits 0 if fix is applied correctly.

set -e

# Check: api_healthy
if grep -qx 'ENABLE_LIVE_EXPORTS=false' etc/export-api/flags.env && grep -qx healthy state/export-api; then
    echo "PASS: api_healthy"
else
    echo "FAIL: api_healthy"
    exit 1
fi

exit 0
