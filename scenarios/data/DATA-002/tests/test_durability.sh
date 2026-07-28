#!/bin/bash
# Durability/persistence test for DATA-002
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: data_preserved
if grep -qx '1,ada@example.com' var/db/users.csv && grep -qx '2,linus@example.com' var/db/users.csv; then
    echo "PASS: data_preserved"
else
    echo "FAIL: data_preserved"
    exit 1
fi

exit 0
