#!/bin/bash
# Durability/persistence test for SEC-006
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: cors_persisted
if grep -qx "ALLOWED_ORIGINS=https://portal.example.internal" etc/web-gateway/cors.env; then
    echo "PASS: cors_persisted"
else
    echo "FAIL: cors_persisted"
    exit 1
fi

exit 0
