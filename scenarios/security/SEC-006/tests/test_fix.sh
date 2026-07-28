#!/bin/bash
# Fix verification test for SEC-006
# Exits 0 if fix is applied correctly.

set -e

# Check: cors_restricted
if grep -qx "ALLOWED_ORIGINS=https://portal.example.internal" etc/web-gateway/cors.env; then
    echo "PASS: cors_restricted"
else
    echo "FAIL: cors_restricted"
    exit 1
fi

# Check: gateway_secure
if grep -qx secure state/web-gateway; then
    echo "PASS: gateway_secure"
else
    echo "FAIL: gateway_secure"
    exit 1
fi

exit 0
