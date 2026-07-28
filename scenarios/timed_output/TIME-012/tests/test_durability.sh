#!/bin/bash
# Durability/persistence test for TIME-012
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: next_policy_updated
if grep -qx skip_duplicate var/lib/dst-job/next-policy.txt && grep -qx healthy state/dst-job; then
    echo "PASS: next_policy_updated"
else
    echo "FAIL: next_policy_updated"
    exit 1
fi

exit 0
