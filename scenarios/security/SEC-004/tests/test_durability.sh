#!/bin/bash
# Durability/persistence test for SEC-004
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: secret_unchanged
if cmp -s etc/demo-api/credentials.env baseline/credentials.env; then
    echo "PASS: secret_unchanged"
else
    echo "FAIL: secret_unchanged"
    exit 1
fi

exit 0
