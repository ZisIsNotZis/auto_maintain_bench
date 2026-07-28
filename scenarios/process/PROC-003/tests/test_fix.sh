#!/bin/bash
# Fix verification test for PROC-003
# Exits 0 if fix is applied correctly.

set -e

# Check: reaper_enabled
if grep -qx 'REAP_CHILDREN=true' etc/demo-api/reaper.env; then
    echo "PASS: reaper_enabled"
else
    echo "FAIL: reaper_enabled"
    exit 1
fi

# Check: zombies_cleared
if grep -qx '0' state/zombie-count; then
    echo "PASS: zombies_cleared"
else
    echo "FAIL: zombies_cleared"
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
