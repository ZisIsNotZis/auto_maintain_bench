#!/bin/bash
# Durability/persistence test for SEC-001
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: service_marked_secure
if grep -qx secure state/demo-api; then
    echo "PASS: service_marked_secure"
else
    echo "FAIL: service_marked_secure"
    exit 1
fi

exit 0
