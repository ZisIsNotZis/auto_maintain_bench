#!/bin/bash
# Durability/persistence test for SEC-002
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: gateway_secure
if grep -qx secure state/auth-gateway; then
    echo "PASS: gateway_secure"
else
    echo "FAIL: gateway_secure"
    exit 1
fi

exit 0
