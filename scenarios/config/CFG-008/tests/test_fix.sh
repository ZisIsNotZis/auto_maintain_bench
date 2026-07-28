#!/bin/bash
# Fix verification test for CFG-008
# Exits 0 if fix is applied correctly.

set -e

# Check: config_valid
if grep -qx 'PLUGIN_API_VERSION=v2' etc/demo-api/plugin.env; then
    echo "PASS: config_valid"
else
    echo "FAIL: config_valid"
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
