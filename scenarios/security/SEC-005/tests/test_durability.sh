#!/bin/bash
# Durability/persistence test for SEC-005
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: report_api_secure
if grep -qx secure state/report-api; then
    echo "PASS: report_api_secure"
else
    echo "FAIL: report_api_secure"
    exit 1
fi

exit 0
