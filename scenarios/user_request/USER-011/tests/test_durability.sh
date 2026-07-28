#!/bin/bash
# Durability/persistence test for USER-011
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: data_preserved
if grep -qx '9001,finance' var/data/customer_exports.csv; then
    echo "PASS: data_preserved"
else
    echo "FAIL: data_preserved"
    exit 1
fi

exit 0
