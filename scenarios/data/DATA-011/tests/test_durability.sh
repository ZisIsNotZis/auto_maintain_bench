#!/bin/bash
# Durability/persistence test for DATA-011
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: checkpoint_enabled
if grep -qx 'AUTO_CHECKPOINT=1' etc/db/checkpoint.env; then
    echo "PASS: checkpoint_enabled"
else
    echo "FAIL: checkpoint_enabled"
    exit 1
fi

exit 0
