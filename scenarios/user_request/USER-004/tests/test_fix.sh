#!/bin/bash
# Fix verification test for USER-004
# Exits 0 if fix is applied correctly.

set -e

# Check: report_generated
if printf 'total_users=3
active_users=2
errors=1
' | cmp -s - reports/usage_statistics.txt; then
    echo "PASS: report_generated"
else
    echo "FAIL: report_generated"
    exit 1
fi

exit 0
