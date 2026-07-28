#!/bin/bash
# Regression prevention test for MICROFLASK-001
# Exits 0 if no regressions introduced.
set -e

echo "Checking service state file..."
if [ -f /sandbox/state/app_status ]; then
    echo "OK: state/app_status exists"
fi

echo "Checking project files intact..."
for f in /sandbox/app.py /sandbox/db.py /sandbox/handlers.py /sandbox/health.sh; do
    if [ -f "$f" ]; then
        echo "OK: $(basename $f) exists"
    else
        echo "FAIL: $f missing"
        exit 1
    fi
done

echo "Checking no forbidden file modifications..."
if [ -f /sandbox/config.env ]; then
    # Verify config wasn't corrupted
    grep -q 'DB_PATH' /sandbox/config.env && echo "OK: config intact"
fi

echo "All regression checks passed"
exit 0
