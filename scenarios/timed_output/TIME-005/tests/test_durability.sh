#!/bin/bash
# Durability/persistence test for TIME-005
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: app_loader_healthy
if grep -qx healthy state/app-loader; then
    echo "PASS: app_loader_healthy"
else
    echo "FAIL: app_loader_healthy"
    exit 1
fi

exit 0
