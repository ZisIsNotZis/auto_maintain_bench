#!/bin/bash
# Fix verification test for TIME-012
# Exits 0 if fix is applied correctly.

set -e

# Check: dst_policy_fixed
if grep -qx "DST_DUPLICATE_POLICY=skip_duplicate" etc/dst-job/schedule.env; then
    echo "PASS: dst_policy_fixed"
else
    echo "FAIL: dst_policy_fixed"
    exit 1
fi

# Check: history_preserved
if cmp -s var/lib/dst-job/run-history.log baseline/run-history.log; then
    echo "PASS: history_preserved"
else
    echo "FAIL: history_preserved"
    exit 1
fi

exit 0
