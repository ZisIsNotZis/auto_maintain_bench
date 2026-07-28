#!/bin/bash
# Durability/persistence test for DISK-005
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: checkpoint_enabled
if grep -qx 'CHECKPOINT_ON_RESTART=true' etc/demo-api/sqlite.env; then
    echo "PASS: checkpoint_enabled"
else
    echo "FAIL: checkpoint_enabled"
    exit 1
fi

exit 0
