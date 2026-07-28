#!/bin/bash
# Durability/persistence test for TIME-011
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: report_cron_healthy
if grep -qx healthy state/report-cron; then
    echo "PASS: report_cron_healthy"
else
    echo "FAIL: report_cron_healthy"
    exit 1
fi

exit 0
