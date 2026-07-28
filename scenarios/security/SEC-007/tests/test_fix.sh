#!/bin/bash
# Fix verification test for SEC-007
# Exits 0 if fix is applied correctly.

set -e

# Check: staged_cert_selected
if grep -qx "CERT_PATH=etc/auth-gateway/staged.pem" etc/auth-gateway/tls.env; then
    echo "PASS: staged_cert_selected"
else
    echo "FAIL: staged_cert_selected"
    exit 1
fi

# Check: gateway_healthy
if grep -qx healthy state/auth-gateway; then
    echo "PASS: gateway_healthy"
else
    echo "FAIL: gateway_healthy"
    exit 1
fi

exit 0
