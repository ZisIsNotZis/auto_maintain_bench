#!/bin/bash
# Fix verification test for DATA-012
# Exits 0 if fix is applied correctly.

set -e

# Check: sql_rows_updated
if grep -qx 'mode=0640' var/db/batch-results.acl; then
    echo "PASS: sql_rows_updated"
else
    echo "FAIL: sql_rows_updated"
    exit 1
fi

# Check: api_healthy
if grep -qx healthy state/batch-reader; then
    echo "PASS: api_healthy"
else
    echo "FAIL: api_healthy"
    exit 1
fi

exit 0
