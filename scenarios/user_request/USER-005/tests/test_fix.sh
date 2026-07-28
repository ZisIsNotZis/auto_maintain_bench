#!/bin/bash
# Fix verification test for USER-005
# Exits 0 if fix is applied correctly.

set -e

# Check: sql_rows_updated
if grep -qx '301,reviewed' var/data/records.csv && grep -qx '302,reviewed' var/data/records.csv && grep -qx '303,hold' var/data/records.csv; then
    echo "PASS: sql_rows_updated"
else
    echo "FAIL: sql_rows_updated"
    exit 1
fi

exit 0
