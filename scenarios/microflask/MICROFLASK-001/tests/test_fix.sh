#!/bin/bash
# Fix verification test for MICROFLASK-001
# Exits 0 if both bugs are fixed.
set -e

# Check 1: Connection leak fixed (db.py must close connections)
echo "Checking connection leak fix..."
if grep -F 'conn.close' /sandbox/db.py || grep -F 'with sqlite3.connect' /sandbox/db.py; then
    echo "PASS: connection leak fixed"
else
    echo "FAIL: db.py still does not close connections"
    exit 1
fi

# Check 2: Pagination fixed (handlers.py must use (page-1) offset)
echo "Checking pagination fix..."
if grep -F 'page - 1' /sandbox/handlers.py; then
    echo "PASS: pagination fixed"
else
    echo "FAIL: handlers.py still has wrong pagination"
    exit 1
fi

# Check 3: Service is healthy
echo "Checking service health..."
if [ -f /sandbox/state/app_status ] && grep -qx healthy /sandbox/state/app_status; then
    echo "PASS: service healthy"
else
    echo "FAIL: service not healthy"
    exit 1
fi

echo "All fix checks passed"
exit 0
