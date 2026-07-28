#!/bin/bash
# Durability/persistence test for TIME-008
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: expiry_extended
if grep -qx "expires_at=2026-07-23T06:40:00Z" var/lib/token-renewer/token.meta && grep -qx healthy state/token-renewer; then
    echo "PASS: expiry_extended"
else
    echo "FAIL: expiry_extended"
    exit 1
fi

exit 0
