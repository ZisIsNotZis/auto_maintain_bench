#!/bin/bash
# Fix verification test for CFG-010
# Exits 0 if fix is applied correctly.

set -e

# Check: config_valid
if grep -qx 'API_ENDPOINT=https://us-east.internal.example' etc/demo-api/endpoint.env; then
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
