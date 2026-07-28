#!/bin/bash
# Fix verification test for DATA-001
# Exits 0 if fix is applied correctly.

set -e

# Check: sql_rows_updated
if awk -F, 'NR>1 && ($1=="1001" || $1=="1002" || $1=="1009"){if($3!="priority") exit 1; found++} END{exit(found==3?0:1)}' var/db/accounts.csv; then
    echo "PASS: sql_rows_updated"
else
    echo "FAIL: sql_rows_updated"
    exit 1
fi

# Check: api_healthy
if grep -qx healthy state/billing-api; then
    echo "PASS: api_healthy"
else
    echo "FAIL: api_healthy"
    exit 1
fi

exit 0
