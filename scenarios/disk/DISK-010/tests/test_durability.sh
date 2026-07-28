#!/bin/bash
# Durability/persistence test for DISK-010
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: atomic_writes_enabled
if grep -qx 'ATOMIC_WRITES=true' etc/demo-api/write.env; then
    echo "PASS: atomic_writes_enabled"
else
    echo "FAIL: atomic_writes_enabled"
    exit 1
fi

exit 0
