#!/bin/bash
# Durability/persistence test for MICROFLASK-001
# Exits 0 if fix persists (e.g. after restart).
set -e

echo "Checking pagination fix persisted..."
if grep -F 'page - 1' /sandbox/handlers.py; then
    echo "PASS: pagination fix persisted"
else
    echo "FAIL: pagination fix not durable"
    exit 1
fi

echo "Checking connection leak fix persisted..."
if grep -F 'conn.close' /sandbox/db.py || grep -F 'with sqlite3.connect' /sandbox/db.py; then
    echo "PASS: connection leak fix persisted"
else
    echo "FAIL: connection leak fix not durable"
    exit 1
fi

echo "All durability checks passed"
exit 0
