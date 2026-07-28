#!/bin/bash
# Fix verification test for DATA-006
# Exits 0 if fix is applied correctly.

set -e

# Check: sql_rows_updated
if [ "$(grep -c '^evt_2001,41,done$' var/db/events.csv)" = '1' ] && [ "$(wc -l < var/db/events.csv)" = '3' ]; then
    echo "PASS: sql_rows_updated"
else
    echo "FAIL: sql_rows_updated"
    exit 1
fi

exit 0
