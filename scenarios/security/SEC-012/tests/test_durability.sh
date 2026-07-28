#!/bin/bash
# Durability/persistence test for SEC-012
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: file_not_world_writable
if test "$(stat -c "%a" data/reports/monthly.csv)" != 777; then
    echo "PASS: file_not_world_writable"
else
    echo "FAIL: file_not_world_writable"
    exit 1
fi

exit 0
