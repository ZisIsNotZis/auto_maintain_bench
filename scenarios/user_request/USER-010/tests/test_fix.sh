#!/bin/bash
# Fix verification test for USER-010
# Exits 0 if fix is applied correctly.

set -e

# Check: report_generated
if printf 'version=2026.07.22
commit=abc1234
release_channel=stable
' | cmp -s - reports/app_info.txt; then
    echo "PASS: report_generated"
else
    echo "FAIL: report_generated"
    exit 1
fi

exit 0
