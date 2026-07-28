#!/bin/bash
# Durability/persistence test for PROC-009
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: lock_ttl_persisted
if grep -qx 'LOCKFILE_MAX_AGE_S=60' etc/demo-api/lock.env; then
    echo "PASS: lock_ttl_persisted"
else
    echo "FAIL: lock_ttl_persisted"
    exit 1
fi

exit 0
