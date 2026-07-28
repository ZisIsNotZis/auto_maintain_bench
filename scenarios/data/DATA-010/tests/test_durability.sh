#!/bin/bash
# Durability/persistence test for DATA-010
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: data_preserved
if grep -qx '5001,19.99' var/db/orders.csv && grep -qx '5002,42.00' var/db/orders.csv; then
    echo "PASS: data_preserved"
else
    echo "FAIL: data_preserved"
    exit 1
fi

exit 0
