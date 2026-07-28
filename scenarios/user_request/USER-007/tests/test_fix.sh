#!/bin/bash
# Fix verification test for USER-007
# Exits 0 if fix is applied correctly.

set -e

# Check: api_healthy
if grep -qx 'ENABLE_BETA_CHECKOUT=true' etc/web/flags.env && grep -qx healthy state/web-frontend; then
    echo "PASS: api_healthy"
else
    echo "FAIL: api_healthy"
    exit 1
fi

exit 0
