#!/bin/bash
# Fix verification test for SEC-003
# Exits 0 if fix is applied correctly.

set -e

# Check: debug_endpoint_disabled
if grep -qx "DEBUG_ENDPOINT=disabled" etc/debug-proxy/security.env; then
    echo "PASS: debug_endpoint_disabled"
else
    echo "FAIL: debug_endpoint_disabled"
    exit 1
fi

# Check: proxy_secure
if grep -qx secure state/debug-proxy; then
    echo "PASS: proxy_secure"
else
    echo "FAIL: proxy_secure"
    exit 1
fi

exit 0
