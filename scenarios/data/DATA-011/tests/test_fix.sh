#!/bin/bash
# Fix verification test for DATA-011
# Exits 0 if fix is applied correctly.

set -e

# Check: wal_cleared
if test ! -e var/db/app.wal; then
    echo "PASS: wal_cleared"
else
    echo "FAIL: wal_cleared"
    exit 1
fi

# Check: api_healthy
if grep -qx healthy state/sqlite-proxy; then
    echo "PASS: api_healthy"
else
    echo "FAIL: api_healthy"
    exit 1
fi

exit 0
