#!/bin/bash
# Fix verification test for DATA-008
# Exits 0 if fix is applied correctly.

set -e

# Check: sql_rows_updated
if grep -qx '1002,active' var/db/profiles.csv && grep -qx '1003,pending' var/db/profiles.csv && [ "$(wc -l < var/db/profiles.csv)" = '4' ]; then
    echo "PASS: sql_rows_updated"
else
    echo "FAIL: sql_rows_updated"
    exit 1
fi

exit 0
