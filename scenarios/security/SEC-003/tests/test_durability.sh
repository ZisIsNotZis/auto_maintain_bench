#!/bin/bash
# Durability/persistence test for SEC-003
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: setting_persisted
if grep -qx "DEBUG_ENDPOINT=disabled" etc/debug-proxy/security.env; then
    echo "PASS: setting_persisted"
else
    echo "FAIL: setting_persisted"
    exit 1
fi

exit 0
